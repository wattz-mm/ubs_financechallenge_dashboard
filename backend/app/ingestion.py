from datetime import datetime, timedelta, timezone
from uuid import uuid4
import asyncio
import time
from urllib.parse import quote_plus
import xml.etree.ElementTree as ET

import httpx

from .ai import classify_category, dedupe_headlines, sentiment_label, sentiment_score
from .config import settings
from .sourced_data import STOCK_UNIVERSE, sourced_stock_rows


class IngestionService:
    def __init__(self):
        self.timeout = httpx.Timeout(10.0)
        self._last_gdelt_request = 0.0

    async def fetch_headlines(self) -> list[dict]:
        queries = [
            "China grid investment hydropower nuclear wind turbine renewable energy",
            "China pumped storage nuclear approvals State Grid renewable integration",
            "China offshore wind turbine margin pricing pressure",
            "China electricity demand grid investment data center power demand",
        ]
        fetched = await asyncio.gather(
            *[self._fetch_google_news_rss(query, maxrecords=25) for query in queries],
            self._fetch_newsapi(" OR ".join(queries[:2]), maxrecords=40),
            self._fetch_gdelt("(China grid investment OR China hydropower OR China nuclear power OR China wind turbine OR China renewable energy OR China coal displacement OR China pumped storage OR State Grid)", maxrecords=60),
        )
        normalized = []
        for item in [item for rows in fetched for item in rows]:
            normalized.append(self._normalize_headline(item))
        return dedupe_headlines(normalized)[:90]

    async def fetch_company_headlines(self) -> dict[str, list[dict]]:
        companies = {
            "1072.HK": [
                '("Dongfang Electric" OR "Dongfang Electric Corporation" OR "1072.HK")',
                '("东方电气" OR "东方电气集团")',
                '("Dongfang Electric" AND (hydro OR nuclear OR turbine OR generator OR grid))',
            ],
            "2727.HK": [
                '("Shanghai Electric" OR "Shanghai Electric Group" OR "2727.HK")',
                '("上海电气" OR "上海电气集团")',
                '("Shanghai Electric" AND (wind OR turbine OR margin OR equipment OR offshore))',
            ],
        }
        result = {}
        for ticker, queries in companies.items():
            fetched = []
            for query in queries:
                fetched.append(await self._fetch_google_news_rss(query, maxrecords=15))
                fetched.append(await self._fetch_newsapi(query, maxrecords=12))
                fetched.append(await self._fetch_gdelt(query, maxrecords=12))
            live = [item for rows in fetched for item in rows]
            normalized = []
            for item in live:
                normalized.append(self._normalize_headline(item, region="China", category="Company sentiment"))
            result[ticker] = dedupe_headlines(normalized)[:24]
        return result

    def _normalize_headline(self, item: dict, region: str | None = None, category: str | None = None) -> dict:
        title = item["title"]
        score = item.get("sentiment_score", sentiment_score(title))
        return {
            "id": item.get("id", item.get("url", uuid4().hex)),
            "title": title,
            "source": item.get("source", "Headline source"),
            "url": item.get("url"),
            "published_at": item.get("published_at", datetime.now(timezone.utc)),
            "region": region or item.get("region", self._infer_region(title)),
            "category": category or item.get("category", classify_category(title)),
            "sentiment": item.get("sentiment", sentiment_label(score)),
            "sentiment_score": round(score, 3),
            "summary": item.get("summary", title),
        }

    async def _fetch_google_news_rss(self, query: str, maxrecords: int = 20) -> list[dict]:
        encoded = quote_plus(query)
        url = f"https://news.google.com/rss/search?q={encoded}&hl=en-SG&gl=SG&ceid=SG:en"
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
            root = ET.fromstring(response.text)
        except Exception:
            return []

        rows = []
        for item in root.findall(".//item")[:maxrecords]:
            title = (item.findtext("title") or "").strip()
            if not title:
                continue
            published = item.findtext("pubDate")
            try:
                published_at = datetime.strptime(published or "", "%a, %d %b %Y %H:%M:%S %Z").replace(tzinfo=timezone.utc)
            except Exception:
                published_at = datetime.now(timezone.utc)
            source_node = item.find("source")
            source = source_node.text.strip() if source_node is not None and source_node.text else "Google News RSS"
            link = item.findtext("link")
            rows.append(
                {
                    "id": link or uuid4().hex,
                    "title": title,
                    "source": f"{source} via Google News RSS",
                    "url": link,
                    "published_at": published_at,
                    "region": self._infer_region(title),
                }
            )
        return rows

    async def _fetch_newsapi(self, query: str, maxrecords: int = 20) -> list[dict]:
        if not settings.news_api_key:
            return []
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": query,
            "language": "en",
            "sortBy": "publishedAt",
            "pageSize": min(maxrecords, 100),
            "apiKey": settings.news_api_key,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                articles = response.json().get("articles", [])
        except Exception:
            return []

        rows = []
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            try:
                published_at = datetime.fromisoformat(article.get("publishedAt", "").replace("Z", "+00:00"))
            except Exception:
                published_at = datetime.now(timezone.utc)
            source_name = (article.get("source") or {}).get("name") or "NewsAPI"
            rows.append(
                {
                    "id": article.get("url", uuid4().hex),
                    "title": title,
                    "source": f"{source_name} via NewsAPI",
                    "url": article.get("url"),
                    "published_at": published_at,
                    "region": self._infer_region(title),
                }
            )
        return rows

    async def _fetch_gdelt(self, query: str, maxrecords: int = 50) -> list[dict]:
        elapsed = time.monotonic() - self._last_gdelt_request
        if elapsed < 5.1:
            await asyncio.sleep(5.1 - elapsed)
        self._last_gdelt_request = time.monotonic()
        params = {
            "query": query,
            "mode": "artlist",
            "format": "json",
            "maxrecords": maxrecords,
            "sort": "hybridrel",
            "timespan": "7d",
        }
        url = "https://api.gdeltproject.org/api/v2/doc/doc"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                articles = response.json().get("articles", [])
        except Exception:
            return []

        output = []
        for article in articles:
            title = article.get("title")
            if not title:
                continue
            published = article.get("seendate")
            try:
                published_at = datetime.strptime(published[:14], "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
            except Exception:
                published_at = datetime.now(timezone.utc)
            output.append(
                {
                    "id": article.get("url", uuid4().hex),
                    "title": title,
                    "source": article.get("domain", "GDELT"),
                    "url": article.get("url"),
                    "published_at": published_at,
                    "region": self._infer_region(title),
                }
            )
        return output

    async def fetch_stock_screener(self) -> list[dict]:
        output = sourced_stock_rows()
        for ticker, name, segment in STOCK_UNIVERSE:
            quote = await self._fetch_yahoo_quote(ticker)
            if not quote:
                quote = await self._fetch_stooq_quote(ticker)
            if quote:
                existing = next((row for row in output if row["ticker"] == ticker), None)
                if existing:
                    existing.update(
                        {
                    "ticker": ticker,
                    "name": name,
                    "segment": segment,
                    "price": quote["price"],
                    "changePct": quote["changePct"],
                    "momentum5d": quote["momentum5d"],
                    "volume": quote.get("volume"),
                    "asOf": quote.get("asOf"),
                    "dataSource": quote.get("dataSource"),
                    "sourceUrl": quote.get("sourceUrl"),
                        }
                    )
        return output

    async def _fetch_yahoo_quote(self, symbol: str) -> dict | None:
        period2 = int(datetime.now(timezone.utc).timestamp())
        period1 = int((datetime.now(timezone.utc) - timedelta(days=5)).timestamp())
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"period1": period1, "period2": period2, "interval": "1d"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                result = response.json()["chart"]["result"][0]
                closes = [v for v in result["indicators"]["quote"][0]["close"] if v is not None]
                latest, prev = closes[-1], closes[-2]
                first = closes[0]
                return {
                    "price": round(latest, 2),
                    "changePct": round((latest - prev) / prev * 100, 2),
                    "momentum5d": round((latest - first) / first * 100, 2),
                    "volume": result["indicators"]["quote"][0].get("volume", [None])[-1],
                    "asOf": datetime.now(timezone.utc).isoformat(),
                    "dataSource": "Yahoo chart endpoint",
                    "sourceUrl": f"https://finance.yahoo.com/quote/{symbol}",
                }
        except Exception:
            return None

    async def _fetch_stooq_quote(self, symbol: str) -> dict | None:
        stooq_symbol = symbol.replace(".SS", ".CN").replace(".SZ", ".CN")
        url = "https://stooq.com/q/l/"
        params = {"s": stooq_symbol, "f": "sd2t2ohlcv", "h": "", "e": "csv"}
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
            lines = [line for line in response.text.strip().splitlines() if line]
            if len(lines) < 2 or "N/D" in lines[1]:
                return None
            _, date, time_, open_, high, low, close, volume = lines[1].split(",")
            close_value = float(close)
            open_value = float(open_)
            return {
                "price": round(close_value, 2),
                "changePct": round((close_value - open_value) / open_value * 100, 2) if open_value else 0.0,
                "momentum5d": 0.0,
                "volume": float(volume) if volume and volume != "N/D" else None,
                "asOf": f"{date} {time_}",
                "dataSource": "Stooq quote endpoint",
                "sourceUrl": f"https://stooq.com/q/?s={stooq_symbol}",
            }
        except Exception:
            return None

    def _infer_region(self, title: str) -> str:
        lower = title.lower()
        if "china" in lower or "beijing" in lower or "shanghai" in lower:
            return "China"
        if "europe" in lower or "north sea" in lower:
            return "Europe"
        if "india" in lower:
            return "India"
        if "lng" in lower or "middle east" in lower or "qatar" in lower:
            return "Middle East"
        if "us " in lower or "u.s." in lower or "america" in lower:
            return "North America"
        return "Global"
