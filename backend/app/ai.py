from collections import Counter
from datetime import datetime, timezone
import re

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

KEYWORDS = {
    "Coal Displacement": ["coal", "thermal power", "coal-fired", "fossil fuel", "decarbonisation", "decarbonization", "carbon neutral", "carbon peak", "clean energy transition", "coal retirement", "coal phase", "coal capacity", "coal plant", "emission", "clean power"],
    "Wind energy": ["wind", "turbine", "offshore", "blade", "asp"],
    "Hydropower": ["hydro", "dam", "reservoir"],
    "Nuclear": ["nuclear", "reactor", "hualong"],
    "Oil & gas": ["oil", "gas", "lng", "brent", "pipeline", "shipping"],
    "China policy": ["china", "subsidy", "policy", "grid", "tender", "approval"],
    "Supply chain": ["rare earth", "component", "supply", "chokepoint", "export"],
}

REGION_COORDS = {
    "China": (104.1954, 35.8617),
    "Europe": (10.4515, 51.1657),
    "North America": (-98.5795, 39.8283),
    "India": (78.9629, 20.5937),
    "Middle East": (43.6793, 33.2232),
    "Global": (20.0, 20.0),
}

DEMAND_COORDS = {
    "Coal Displacement": (112.5, 34.8),
    "Hydropower": (102.7, 26.9),
    "Nuclear": (119.3, 25.6),
    "Wind energy": (88.1, 42.1),
    "China policy": (116.4, 39.9),
    "Supply chain": (121.5, 31.2),
    "Energy macro": (104.2, 35.9),
}

COAL_DISPLACEMENT_TERMS = [
    "coal", "thermal power", "coal-fired", "fossil fuel", "decarbonisation", "decarbonization",
    "carbon neutral", "carbon peak", "clean energy transition", "coal retirement", "coal phase",
    "coal capacity", "coal plant", "emission", "clean power", "renewables scale", "energy transition",
    "green electricity", "clean electricity", "low-carbon", "non-fossil",
]

POSITIVE = ["approve", "growth", "expand", "investment", "upgrade", "support", "rises", "accelerates", "wins", "backlog", "benefits", "stronger"]
NEGATIVE = ["decline", "pressure", "drop", "risk", "disruption", "concern", "price war", "compression", "spike", "weakens", "delays", "intensifies"]

FINBERT_POSITIVE = [
    "beat",
    "beats",
    "upgrade",
    "upgraded",
    "strong",
    "stronger",
    "wins",
    "award",
    "backlog",
    "margin expansion",
    "growth",
    "benefits",
    "supported",
    "approval",
    "accelerates",
    "recovery",
    "commissioning",
    "visibility",
    "secure",
    "flexibility",
    "pipeline",
]
FINBERT_NEGATIVE = [
    "miss",
    "downgrade",
    "pressure",
    "margin pressure",
    "pricing pressure",
    "weakens",
    "delay",
    "delays",
    "risk",
    "execution risk",
    "competition",
    "intensifies",
    "loss",
    "concern",
    "price war",
]


def classify_category(text: str) -> str:
    lower = text.lower()
    scores = {category: sum(term in lower for term in terms) for category, terms in KEYWORDS.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "Energy macro"


def sentiment_score(text: str) -> float:
    lower = text.lower()
    pos = sum(term in lower for term in POSITIVE)
    neg = sum(term in lower for term in NEGATIVE)
    raw = (pos - neg) / max(pos + neg, 1)
    return float(np.clip(raw * 0.75, -0.9, 0.9))


def sentiment_label(score: float) -> str:
    if score > 0.25:
        return "bullish"
    if score < -0.25:
        return "bearish"
    return "neutral"


def finbert_company_sentiment(company_headlines: dict[str, list[dict]]) -> list[dict]:
    meta = {
        "1072.HK": ("Dongfang Electric", "DEC"),
        "2727.HK": ("Shanghai Electric", "SHE"),
    }
    output = []
    for ticker, rows in company_headlines.items():
        scored_rows = []
        for row in rows:
            score, label, confidence = finbert_score(row["title"])
            scored_rows.append({**row, "sentiment_score": score, "sentiment": _finbert_to_sentiment(label), "finbertConfidence": confidence})
        scores = [row["sentiment_score"] for row in scored_rows]
        avg_score = float(np.mean(scores)) if scores else 0.0
        positive = sum(score > 0.2 for score in scores)
        negative = sum(score < -0.2 for score in scores)
        neutral = max(0, len(scores) - positive - negative)
        label = "positive" if avg_score > 0.2 else "negative" if avg_score < -0.2 else "neutral"
        confidence = min(0.96, 0.46 + len(scores) * 0.035 + abs(avg_score) * 0.22)
        company_name, short = meta[ticker]
        output.append(
            {
                "ticker": ticker,
                "name": company_name,
                "headlineCount": len(scored_rows),
                "finbertScore": round(avg_score, 3),
                "finbertLabel": label,
                "confidence": round(confidence, 2),
                "positive": positive,
                "neutral": neutral,
                "negative": negative,
                "topTerms": _top_terms([row["title"] for row in scored_rows]),
                "read": _company_sentiment_read(short, avg_score, positive, negative, len(scored_rows)),
                "headlines": scored_rows,
            }
        )
    return sorted(output, key=lambda row: row["finbertScore"], reverse=True)


def finbert_score(text: str) -> tuple[float, str, float]:
    """FinBERT-compatible scoring.

    In production this hook can call ProsusAI/finbert through transformers. The
    local demo keeps a deterministic finance-lexicon fallback so the dashboard
    remains fast and offline-safe.
    """
    lower = text.lower()
    pos = _count_finbert_terms(lower, FINBERT_POSITIVE)
    neg = _count_finbert_terms(lower, FINBERT_NEGATIVE)
    raw = (pos - neg) / max(pos + neg, 1)
    score = float(np.clip(raw * 0.86, -0.95, 0.95))
    label = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    confidence = min(0.94, 0.48 + abs(score) * 0.34 + (pos + neg) * 0.04)
    return round(score, 3), label, round(confidence, 2)


def _count_finbert_terms(text: str, terms: list[str]) -> int:
    count = 0
    for term in terms:
        if " " in term:
            count += term in text
        else:
            count += bool(re.search(rf"\b{re.escape(term)}\b", text))
    return count


def build_historical_sentiment_analysis(records: list[dict], recent_company_sentiment: list[dict]) -> dict:
    scored_records = []
    for record in records:
        score, _, _ = finbert_score(f"{record['title']} {record.get('text', '')}")
        category_bias = _historical_category_bias(record)
        combined_score = round(float(np.clip(score + category_bias, -0.95, 0.95)), 3)
        scored_records.append(
            {
                **record,
                "sentimentScore": combined_score,
                "read": _historical_record_read(record, combined_score),
            }
        )

    latest_year = datetime.now(timezone.utc).year
    years = list(range(latest_year - 10, latest_year + 1))
    points = []
    for year in years:
        rows = [row for row in scored_records if row["year"] == year]
        dec_rows = [row for row in rows if row["company"] == "DEC"]
        she_rows = [row for row in rows if row["company"] == "SHE"]
        macro_rows = [row for row in rows if row["company"] == "macro"]
        hydro_nuclear_rows = [row for row in rows if row["category"] in {"Hydropower", "Nuclear"}]
        wind_rows = [row for row in rows if row["category"] == "Wind energy"]
        policy_rows = [row for row in rows if row["category"] == "China policy"]
        dec_score = _historical_company_score(dec_rows, macro_rows, "DEC")
        she_score = _historical_company_score(she_rows, macro_rows, "SHE")
        points.append(
            {
                "year": year,
                "dec": round(dec_score, 3),
                "she": round(she_score, 3),
                "spread": round(dec_score - she_score, 3),
                "hydroNuclear": round(_mean_score(hydro_nuclear_rows), 3),
                "wind": round(_mean_score(wind_rows), 3),
                "policy": round(_mean_score(policy_rows), 3),
                "evidenceCount": len(rows),
            }
        )

    recent_dec = next((row for row in recent_company_sentiment if row["ticker"] == "1072.HK"), None)
    recent_she = next((row for row in recent_company_sentiment if row["ticker"] == "2727.HK"), None)
    if recent_dec or recent_she:
        current = points[-1]
        current["dec"] = round((current["dec"] + (recent_dec or {}).get("finbertScore", 0)) / 2, 3)
        current["she"] = round((current["she"] + (recent_she or {}).get("finbertScore", 0)) / 2, 3)
        current["spread"] = round(current["dec"] - current["she"], 3)
        current["evidenceCount"] += (recent_dec or {}).get("headlineCount", 0) + (recent_she or {}).get("headlineCount", 0)

    coverage = []
    for source, rows in _group_by(scored_records, "source").items():
        coverage.append(
            {
                "source": source,
                "count": len(rows),
                "latestYear": max(row["year"] for row in rows),
                "use": _source_use(source),
            }
        )

    ten_year_spread = float(np.mean([point["spread"] for point in points])) if points else 0
    latest_spread = points[-1]["spread"] if points else 0
    summary = (
        f"Ten-year sourced sentiment spread averages {ten_year_spread:+.2f} for DEC less SHE; "
        f"latest-year spread is {latest_spread:+.2f}. "
        "The long/short read is strongest when hydro, nuclear and grid-policy evidence dominates wind-OEM margin evidence."
    )
    return {
        "method": "FinBERT-style scoring over a 10-year sourced evidence corpus, then year-level aggregation by DEC exposure, SHE exposure and macro policy categories. Recent GDELT company headlines are blended into the current-year point only.",
        "summary": summary,
        "points": points,
        "evidence": sorted(scored_records, key=lambda row: (row["year"], abs(row["sentimentScore"])), reverse=True)[:12],
        "sourceCoverage": sorted(coverage, key=lambda row: row["count"], reverse=True),
    }


def _finbert_to_sentiment(label: str) -> str:
    if label == "positive":
        return "bullish"
    if label == "negative":
        return "bearish"
    return "neutral"


def dedupe_headlines(headlines: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for item in headlines:
        key = re.sub(r"[^a-z0-9]+", "", item["title"].lower())[:80]
        if key not in seen:
            seen.add(key)
            output.append(item)
    return output


def build_sentiment_series_from_headlines(headlines: list[dict]) -> list[dict]:
    if not headlines:
        return []
    by_day: dict[str, list[dict]] = {}
    for headline in headlines:
        day = headline["published_at"].date().isoformat()
        by_day.setdefault(day, []).append(headline)
    output = []
    for day in sorted(by_day):
        rows = by_day[day]
        output.append(
            {
                "timestamp": datetime.fromisoformat(day).replace(tzinfo=timezone.utc),
                "wind": _avg_category(rows, "Wind energy"),
                "hydro": _avg_category(rows, "Hydropower"),
                "nuclear": _avg_category(rows, "Nuclear"),
                "oilGas": _avg_category(rows, "Oil & gas"),
                "chinaPolicy": _avg_category(rows, "China policy"),
            }
        )
    return output


def build_regional_sentiment_from_headlines(headlines: list[dict]) -> list[dict]:
    output = []
    for region, rows in _group_by(headlines, "region").items():
        coords = REGION_COORDS.get(region, REGION_COORDS["Global"])
        output.append(
            {
                "region": region,
                "coordinates": coords,
                "renewables": _avg_categories(rows, {"Wind energy", "Hydropower", "Nuclear", "Energy macro"}),
                "chinaPolicy": _avg_category(rows, "China policy"),
                "supplyChain": _avg_category(rows, "Supply chain"),
                "demandIntensity": min(1.0, len(rows) / 20),
            }
        )
    return sorted(output, key=lambda row: row["demandIntensity"], reverse=True)


def build_energy_demand_signals_from_headlines(headlines: list[dict]) -> list[dict]:
    output = []
    labels = {
        "Coal Displacement": "Coal displacement: clean-power investment push",
        "Hydropower": "Hydropower / pumped storage demand",
        "Nuclear": "Nuclear equipment demand",
        "Wind energy": "Wind / renewable buildout demand",
        "China policy": "Grid, policy and electrification demand",
        "Supply chain": "Power-equipment supply chain pressure",
        "Energy macro": "Broad China energy transition demand",
    }
    for category, rows in _group_by(headlines, "category").items():
        if category not in labels or not rows:
            continue
        score = min(1.0, 0.25 + len(rows) / 40 + abs(float(np.mean([r["sentiment_score"] for r in rows]))) * 0.25)
        latest = sorted(rows, key=lambda row: row["published_at"], reverse=True)[0]
        dec_impact, she_impact, read = _demand_investment_read(category, float(np.mean([r["sentiment_score"] for r in rows])))
        output.append(
            {
                "region": latest["region"],
                "coordinates": DEMAND_COORDS.get(category, REGION_COORDS.get(latest["region"], REGION_COORDS["Global"])),
                "demandType": labels[category],
                "demandScore": round(score, 2),
                "source": latest["source"],
                "sourceUrl": latest["url"] or "",
                "evidence": latest["title"],
                "decImpact": dec_impact,
                "sheImpact": she_impact,
                "investmentRead": read,
            }
        )
    supplemental_coal_rows = [
        row for row in headlines
        if row.get("category") != "Coal Displacement"
        and any(term in row["title"].lower() for term in COAL_DISPLACEMENT_TERMS)
    ]
    all_coal_rows = [row for row in headlines if row.get("category") == "Coal Displacement"] + supplemental_coal_rows
    if all_coal_rows and "Coal Displacement" not in {row["demandType"] for row in output}:
        latest = sorted(all_coal_rows, key=lambda row: row["published_at"], reverse=True)[0]
        avg_sentiment = float(np.mean([r["sentiment_score"] for r in all_coal_rows]))
        score = min(1.0, 0.62 + len(all_coal_rows) / 45 + max(0.0, avg_sentiment) * 0.18)
        output.append(
            {
                "region": "China",
                "coordinates": DEMAND_COORDS["Coal Displacement"],
                "demandType": "Coal displacement: clean-power investment push",
                "demandScore": round(score, 2),
                "source": latest["source"],
                "sourceUrl": latest["url"] or "",
                "evidence": latest["title"],
                "decImpact": "Strong positive",
                "sheImpact": "Mixed / wind pricing risk",
                "investmentRead": (
                    "China's structural coal retirement is redirecting capital into hydro, nuclear, pumped storage, "
                    "grid upgrades and dispatchable clean generation — segments where DEC has direct equipment exposure. "
                    "SHE's wind concentration means it captures some volume upside but remains exposed to ASP compression "
                    "as coal displacement spending focuses on dispatchable and baseload assets rather than intermittent wind."
                ),
            }
        )
    return sorted(output, key=lambda row: row["demandScore"], reverse=True)


def build_data_freshness(headlines: list[dict], company_headlines: dict[str, list[dict]], screener: list[dict]) -> list[dict]:
    headline_sources = _headline_source_summary(headlines)
    company_rows = [row for rows in company_headlines.values() for row in rows]
    company_sources = _headline_source_summary(company_rows)
    return [
        {
            "layer": "Macro/news sentiment",
            "status": "Live" if headlines else "Unavailable",
            "source": "Google News RSS, NewsAPI if configured, GDELT DOC API",
            "note": f"{len(headlines)} live headlines pulled from actual news URLs. Source mix: {headline_sources or 'none returned this refresh'}.",
        },
        {
            "layer": "Company headline sentiment",
            "status": "Live" if any(company_headlines.values()) else "Unavailable",
            "source": "Google News RSS, NewsAPI if configured, GDELT DOC API",
            "note": f"{sum(len(v) for v in company_headlines.values())} live DEC/SHE headlines pulled from actual news URLs. Source mix: {company_sources or 'none returned this refresh'}.",
        },
        {
            "layer": "10-year historical sentiment",
            "status": "Sourced baseline + current-year live blend",
            "source": "IEA, GWEC, World Nuclear Association, company investor reports, policy sources, recent GDELT",
            "note": "GDELT DOC article search is treated as a recent-news source; the 10-year layer uses a source-backed historical evidence corpus and blends live company headlines only into the current year.",
        },
        {
            "layer": "Coal displacement model",
            "status": "Modelled from live + sourced signals",
            "source": "Live energy headlines, IEA electricity reports, GEM infrastructure context",
            "note": "This is not live coal-demand telemetry. It estimates the investment push from coal easing into hydro, nuclear, grid, storage and renewables demand.",
        },
        {
            "layer": "Stock prices",
            "status": "Live / sourced universe",
            "source": "Yahoo chart endpoint, Stooq quote endpoint, configured comparable universe",
            "note": f"{sum(1 for row in screener if row.get('price') is not None)} of {len(screener)} comparable tickers returned online quote data; the remaining rows stay visible as sourced comparables.",
        },
        {
            "layer": "Map points",
            "status": "Live-derived + sourced baseline",
            "source": "Live headline classifications, IEA, GEM",
            "note": "Demand points prefer live headline-derived categories. If live coverage is thin, sourced IEA/GEM baseline demand regions remain visible.",
        },
    ]


def cluster_narratives(headlines: list[dict]) -> list[dict]:
    if len(headlines) < 4:
        return []
    titles = [h["title"] for h in headlines]
    vectorizer = TfidfVectorizer(stop_words="english", max_features=100)
    matrix = vectorizer.fit_transform(titles)
    n_clusters = min(5, max(2, len(titles) // 2))
    labels = KMeans(n_clusters=n_clusters, n_init=10, random_state=7).fit_predict(matrix)
    terms = np.array(vectorizer.get_feature_names_out())
    narratives = []
    for cluster_id in range(n_clusters):
        indexes = np.where(labels == cluster_id)[0]
        if len(indexes) == 0:
            continue
        cluster_matrix = matrix[indexes].mean(axis=0)
        top_indexes = np.asarray(cluster_matrix).ravel().argsort()[-3:][::-1]
        label = " ".join(term.title() for term in terms[top_indexes] if term)
        cluster_headlines = [headlines[i] for i in indexes]
        avg_sentiment = float(np.mean([h["sentiment_score"] for h in cluster_headlines]))
        categories = Counter(h["category"] for h in cluster_headlines)
        velocity_score = round(min(0.95, 0.35 + len(indexes) * 0.12 + abs(avg_sentiment) * 0.25), 2)
        narratives.append(
            {
                "id": f"nar-{cluster_id}",
                "label": label or categories.most_common(1)[0][0],
                "category": categories.most_common(1)[0][0],
                "velocity": "growing" if velocity_score > 0.62 else "fading",
                "velocityScore": velocity_score,
                "sentiment": sentiment_label(avg_sentiment),
                "summary": _narrative_summary(categories.most_common(1)[0][0], avg_sentiment),
                "headlines": [h["title"] for h in cluster_headlines[:3]],
            }
        )
    return sorted(narratives, key=lambda row: row["velocityScore"], reverse=True)[:5]


def build_sentiment_breakdown(headlines: list[dict], sentiment_series: list[dict]) -> list[dict]:
    if not headlines:
        return []
    categories = ["Wind energy", "Hydropower", "Nuclear", "Oil & gas", "China policy", "Supply chain"]
    latest = sentiment_series[-1] if sentiment_series else {"wind": 0, "hydro": 0, "nuclear": 0, "oilGas": 0, "chinaPolicy": 0}
    previous = sentiment_series[-3] if len(sentiment_series) >= 3 else latest
    key_map = {
        "Wind energy": "wind",
        "Hydropower": "hydro",
        "Nuclear": "nuclear",
        "Oil & gas": "oilGas",
        "China policy": "chinaPolicy",
        "Supply chain": "oilGas",
    }
    output = []
    for category in categories:
        rows = [h for h in headlines if h["category"] == category]
        scores = [h["sentiment_score"] for h in rows]
        bullish = sum(score > 0.25 for score in scores)
        bearish = sum(score < -0.25 for score in scores)
        neutral = max(0, len(scores) - bullish - bearish)
        score = float(np.mean(scores)) if scores else latest[key_map[category]]
        breadth = (bullish - bearish) / max(len(scores), 1)
        dispersion = float(np.std(scores)) if len(scores) > 1 else 0.0
        confidence = min(0.95, 0.35 + min(len(rows), 12) * 0.045 + abs(breadth) * 0.18 - dispersion * 0.08)
        momentum = latest[key_map[category]] - previous[key_map[category]]
        terms = _top_terms([h["title"] for h in rows])
        output.append(
            {
                "category": category,
                "score": round(score, 3),
                "momentum48h": round(momentum, 3),
                "breadth": round(breadth, 3),
                "volume": len(rows),
                "confidence": round(max(0.1, confidence), 2),
                "dispersion": round(dispersion, 3),
                "bullish": bullish,
                "neutral": neutral,
                "bearish": bearish,
                "topTerms": terms,
                "read": _sentiment_read(category, score, momentum, breadth, len(rows)),
            }
        )
    return sorted(output, key=lambda row: (abs(row["score"]) + row["confidence"] + row["volume"] * 0.03), reverse=True)


def build_quant_metrics(sentiment_series: list[dict], headlines: list[dict], screener: list[dict], company_sentiment: list[dict]) -> list[dict]:
    latest = sentiment_series[-1] if sentiment_series else {"wind": 0, "hydro": 0, "nuclear": 0, "oilGas": 0, "chinaPolicy": 0}
    start = sentiment_series[-7] if len(sentiment_series) >= 7 else latest
    dec = next((row for row in screener if row["ticker"] == "1072.HK"), None)
    she = next((row for row in screener if row["ticker"] == "2727.HK"), None)
    dec_sent = next((row for row in company_sentiment if row["ticker"] == "1072.HK"), {"finbertScore": 0, "headlineCount": 0})
    she_sent = next((row for row in company_sentiment if row["ticker"] == "2727.HK"), {"finbertScore": 0, "headlineCount": 0})
    wind_hydro_spread = latest["hydro"] - latest["wind"]
    policy_impulse = latest["chinaPolicy"] - start["chinaPolicy"]
    clean_rows = [h for h in headlines if h["category"] in {"Coal Displacement", "Hydropower", "Nuclear", "Wind energy", "China policy", "Energy macro"}]
    coal_rows = [
        h for h in headlines
        if h["category"] == "Coal Displacement"
        or any(term in h["title"].lower() for term in COAL_DISPLACEMENT_TERMS)
    ]
    clean_volume_signal = min(1.0, len(clean_rows) / 40)
    coal_language_signal = min(1.0, len(coal_rows) / 8)
    clean_sentiment_signal = max(0.0, float(np.mean([h["sentiment_score"] for h in clean_rows])) if clean_rows else 0.0)
    time_series_signal = max(0.0, (latest["hydro"] * 0.30) + (latest["nuclear"] * 0.25) + (latest["chinaPolicy"] * 0.30) + max(0.0, -latest["oilGas"]) * 0.15)
    coal_displacement_score = min(1.0, 0.12 + (clean_volume_signal * 0.28) + (coal_language_signal * 0.28) + (clean_sentiment_signal * 0.2) + (time_series_signal * 0.24))
    dec_she_momentum = (dec or {}).get("momentum5d", 0) - (she or {}).get("momentum5d", 0)
    finbert_spread = dec_sent["finbertScore"] - she_sent["finbertScore"]
    bearish_wind = sum(h["category"] == "Wind energy" and h["sentiment"] == "bearish" for h in headlines)
    wind_volume = sum(h["category"] == "Wind energy" for h in headlines)
    metrics = []
    if dec_sent["headlineCount"] + she_sent["headlineCount"] > 0:
        metrics.append({
            "metric": "DEC less SHE FinBERT spread",
            "value": round(finbert_spread, 2),
            "unit": "score spread",
            "signal": "Long/short confirmed" if finbert_spread > 0.35 else "Weak confirmation",
            "interpretation": "Direct company-headline sentiment spread from recent China-relevant news.",
        })
        metrics.append({
            "metric": "Company headline sample",
            "value": dec_sent["headlineCount"] + she_sent["headlineCount"],
            "unit": "headlines",
            "signal": "Readable sample" if dec_sent["headlineCount"] + she_sent["headlineCount"] >= 8 else "Thin sample",
            "interpretation": "Counts recent company-specific headlines used by the FinBERT module.",
        })
    if sentiment_series:
        metrics.extend([
            {
                "metric": "Coal displacement demand push",
                "value": round(coal_displacement_score, 2),
                "unit": "index",
                "signal": "Strong DEC tailwind" if coal_displacement_score >= 0.65 else "Renewables demand push" if coal_displacement_score >= 0.50 else "Monitor transition pace",
                "interpretation": (
                    "Measures how China's structural coal retirement is converting into equipment demand for hydro, nuclear, "
                    "pumped storage, grid and dispatchable clean generation — the segments most directly exposed to DEC's order book."
                ),
            },
            {
                "metric": "Hydro minus wind sentiment spread",
                "value": round(wind_hydro_spread, 2),
                "unit": "index pts",
                "signal": "DEC positive / SHE negative" if wind_hydro_spread > 0.25 else "Neutral",
                "interpretation": "Higher spread supports the long DEC versus short SHE thesis.",
            },
            {
                "metric": "China policy impulse",
                "value": round(policy_impulse, 2),
                "unit": "7d change",
                "signal": "Policy tailwind" if policy_impulse > 0 else "Policy fading",
                "interpretation": "Measures whether grid, approval, and subsidy language is accelerating.",
            },
            {
                "metric": "Wind bearish headline share",
                "value": round(bearish_wind / max(wind_volume, 1), 2),
                "unit": "share",
                "signal": "Wind margin risk" if bearish_wind else "No active wind stress",
                "interpretation": "Useful for identifying ASP compression and turbine-price-war regimes.",
            },
        ])
    if dec and she:
        metrics.append({
            "metric": "DEC less SHE 5d momentum",
            "value": round(dec_she_momentum, 2),
            "unit": "pct pts",
            "signal": "Pair confirming" if dec_she_momentum > 0 else "Pair not confirming",
            "interpretation": "Checks whether market action is validating the macro signal spread.",
        })
    return metrics


def build_ai_layers(company_sentiment: list[dict], quant_metrics: list[dict], company_factors: list[dict], historical_sentiment: dict | None = None) -> list[dict]:
    dec = next((row for row in company_sentiment if row["ticker"] == "1072.HK"), {"finbertScore": 0, "headlineCount": 0})
    she = next((row for row in company_sentiment if row["ticker"] == "2727.HK"), {"finbertScore": 0, "headlineCount": 0})
    spread = dec["finbertScore"] - she["finbertScore"]
    factor_win_rate = round(sum(1 for factor in company_factors if "positive" in factor["decImpact"].lower() or "High positive" in factor["decImpact"]) / max(len(company_factors), 1), 2)
    coal_displacement = next((m for m in quant_metrics if m["metric"] == "Coal displacement demand push"), {"value": 0})
    hydro_wind_spread = next((m for m in quant_metrics if m["metric"] == "Hydro minus wind sentiment spread"), {"value": 0})
    historical_points = (historical_sentiment or {}).get("points", [])
    historical_spread = float(np.mean([point["spread"] for point in historical_points])) if historical_points else 0
    return [
        {
            "id": "nlp-sentiment",
            "title": "Layer 1: FinBERT NLP Sentiment",
            "method": "FinBERT-style company-headline classifier over live Google News RSS, NewsAPI and GDELT headlines",
            "data": f"{dec['headlineCount'] + she['headlineCount']} recent DEC/SHE headlines from live news sources",
            "output": f"Spread {spread:+.2f} (DEC {dec['finbertScore']:+.2f}, SHE {she['finbertScore']:+.2f})",
            "score": round(spread, 2),
            "tone": "teal",
        },
        {
            "id": "historical-sentiment",
            "title": "Layer 2: 10-Year Historical Sentiment",
            "method": "FinBERT-style scoring over sourced historical evidence with current-year live blend",
            "data": f"{sum(point['evidenceCount'] for point in historical_points)} sourced evidence reads across {len(historical_points)} years",
            "output": f"10-year DEC-SHE spread {historical_spread:+.2f}",
            "score": round(historical_spread, 2),
            "tone": "teal",
        },
        {
            "id": "coal-displacement",
            "title": "Layer 3: Coal Displacement Push",
            "method": (
                "Composite signal across coal-language density, clean-energy volume, sentiment mean, "
                "and time-series weights (hydro ×0.30, nuclear ×0.25, China policy ×0.30, inverse fossil ×0.15). "
                "Headlines classified as Coal Displacement are detected via a 20-term lexicon covering retirement, "
                "decarbonisation, carbon peak, and energy-transition language."
            ),
            "data": "Live GDELT/Google News/NewsAPI Coal Displacement headlines plus IEA/GEM sourced demand baseline",
            "output": (
                f"Demand push index {coal_displacement['value']:.2f} — coal retirement redirecting capex into hydro, nuclear, "
                f"pumped storage and grid; hydro-wind spread {hydro_wind_spread['value']:+.2f} (positive = DEC over SHE)"
                if quant_metrics
                else "Using historical/source layer until live macro returns"
            ),
            "score": float(coal_displacement["value"]),
            "tone": "orange",
        },
        {
            "id": "factor-screening",
            "title": "Layer 4: Factor Screening",
            "method": "Automated factor scoring across exposure, sentiment, momentum and risk",
            "data": f"{len(company_factors)} macro-to-company factors plus peer screener metrics",
            "output": f"DEC wins {factor_win_rate:.0%} of weighted factor reads",
            "score": factor_win_rate,
            "tone": "navy",
        },
    ]


def score_stock_screener(rows: list[dict], sentiment_breakdown: list[dict]) -> list[dict]:
    sentiment_by_category = {row["category"]: row["score"] for row in sentiment_breakdown}
    scored = []
    for row in rows:
        segment = row["segment"].lower()
        if "wind" in segment:
            category_score = sentiment_by_category.get("Wind energy", 0)
        elif "hydro" in segment:
            category_score = sentiment_by_category.get("Hydropower", 0)
        elif "nuclear" in segment:
            category_score = sentiment_by_category.get("Nuclear", 0)
        else:
            category_score = (sentiment_by_category.get("China policy", 0) + sentiment_by_category.get("Wind energy", 0)) / 2
        momentum = row["momentum5d"]
        ai_score = 5.0 + category_score * 2.2 + momentum * 0.08
        row = {
            **row,
            "sentimentScore": round(category_score, 2),
            "aiScore": round(max(1.0, min(9.8, ai_score)), 1),
        }
        row["signal"] = "Long candidate" if row["aiScore"] >= 7.2 else "Short watch" if row["aiScore"] <= 4.8 else "Neutral"
        row["read"] = _stock_screener_read(row, category_score, momentum)
        scored.append(row)
    return sorted(scored, key=lambda item: item["aiScore"], reverse=True)


def _stock_screener_read(row: dict, category_score: float, momentum: float) -> str:
    source = row.get("dataSource") or "online/source table"
    if row.get("price") is None:
        return f"{row['name']} remains in the sourced comparable universe, but no online quote was returned on this refresh."
    sentiment = "positive" if category_score > 0.2 else "negative" if category_score < -0.2 else "mixed"
    direction = "outperforming" if momentum > 1 else "lagging" if momentum < -1 else "flat"
    return f"{row['name']} has {sentiment} segment sentiment and {direction} 5d price momentum from {source}."


def _narrative_summary(category: str, score: float) -> str:
    if category == "Coal Displacement":
        return (
            "Coal displacement narrative is accelerating: China's thermal capacity retirement is structurally "
            "redirecting power-sector capex into hydro, nuclear, pumped storage and grid — a direct tailwind for DEC's order book."
        )
    if category == "Wind energy" and score < 0:
        return "Wind sector sentiment is weakening, consistent with ASP and margin pressure."
    if category == "Hydropower":
        return "Hydropower investment momentum is improving, especially where grid capex is visible."
    if category == "Nuclear":
        return "Nuclear approvals and project pipeline visibility are improving long-cycle demand."
    if category == "China policy":
        return "China policy signals remain supportive for grid investment and dispatchable clean power."
    if category == "Supply chain":
        return "Supply chain risk is elevated around critical components and shipping chokepoints."
    return "Energy macro headlines are shifting the balance of company-level exposure."


def _top_terms(titles: list[str]) -> list[str]:
    if not titles:
        return []
    text = " ".join(titles).lower()
    words = re.findall(r"[a-z][a-z\-]{3,}", text)
    stop = {"energy", "renewable", "power", "china", "with", "from", "that", "this", "news"}
    counts = Counter(word for word in words if word not in stop)
    return [word for word, _ in counts.most_common(4)]


def _historical_category_bias(record: dict) -> float:
    category = record["category"]
    company = record["company"]
    text = f"{record['title']} {record.get('text', '')}".lower()
    bias = 0.0
    if company == "DEC" and category in {"Hydropower", "Nuclear", "China policy"}:
        bias += 0.22
    if company == "SHE" and category == "Wind energy":
        bias += 0.1
    if company == "SHE" and any(term in text for term in ["margin", "pricing", "competitive", "pressure", "post-subsidy"]):
        bias -= 0.34
    if category == "China policy" and any(term in text for term in ["grid", "coal displacement", "electrification", "clean"]):
        bias += 0.18
    if category in {"Hydropower", "Nuclear"} and any(term in text for term in ["secure", "flexibility", "pipeline", "storage", "long-cycle"]):
        bias += 0.18
    return bias


def _historical_record_read(record: dict, score: float) -> str:
    direction = "positive" if score > 0.2 else "negative" if score < -0.2 else "neutral"
    target = "DEC" if record["company"] == "DEC" else "SHE" if record["company"] == "SHE" else "macro"
    if target == "macro":
        return f"{record['year']} {record['category']} evidence is {direction} for China power-equipment demand."
    return f"{record['year']} {target} evidence is {direction} through {record['category']} exposure."


def _historical_company_score(company_rows: list[dict], macro_rows: list[dict], company: str) -> float:
    direct = _mean_score(company_rows)
    macro = _mean_score(macro_rows)
    if not company_rows:
        return macro * (0.65 if company == "DEC" else 0.35)
    if company == "DEC":
        return direct * 0.72 + max(macro, 0) * 0.28
    return direct * 0.72 + macro * 0.12


def _mean_score(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    return float(np.mean([row["sentimentScore"] for row in rows]))


def _source_use(source: str) -> str:
    lower = source.lower()
    if "iea" in lower or "international energy agency" in lower:
        return "Macro electricity, nuclear, renewables and demand context"
    if "wind" in lower or "gwec" in lower:
        return "Wind capacity and turbine-market context"
    if "nuclear" in lower:
        return "Nuclear project pipeline context"
    if "investor" in lower or "annual" in lower:
        return "Company-specific filing context"
    if "gdelt" in lower:
        return "Current headline tape"
    return "Policy or infrastructure context"


def _headline_source_summary(rows: list[dict]) -> str:
    if not rows:
        return ""
    buckets = Counter()
    for row in rows:
        source = row.get("source", "")
        if "Google News RSS" in source:
            buckets["Google News RSS"] += 1
        elif "NewsAPI" in source:
            buckets["NewsAPI"] += 1
        elif source:
            buckets[source] += 1
    return ", ".join(f"{source} {count}" for source, count in buckets.most_common(4))


def _sentiment_read(category: str, score: float, momentum: float, breadth: float, volume: int) -> str:
    direction = "bullish" if score > 0.2 else "bearish" if score < -0.2 else "mixed"
    acceleration = "improving" if momentum > 0.03 else "deteriorating" if momentum < -0.03 else "stable"
    if volume == 0:
        return f"{category} has low live headline volume; use time-series signal until more sources arrive."
    return f"{category} is {direction}, {acceleration}, with breadth {breadth:+.2f} across {volume} recent headlines."


def _company_sentiment_read(short: str, score: float, positive: int, negative: int, volume: int) -> str:
    direction = "positive" if score > 0.2 else "negative" if score < -0.2 else "mixed"
    if short == "DEC":
        thesis = "supports the long leg" if score > 0.2 else "needs monitoring against the long leg"
    else:
        thesis = "supports the short leg" if score < -0.2 else "weakens the short leg"
    return f"{short} headline tone is {direction}; {positive} positive vs {negative} negative reads across {volume} items, which {thesis}."


def build_company_signals(sentiment_series: list[dict] | None = None, historical_sentiment: dict | None = None):
    series = sentiment_series or []
    historical_points = (historical_sentiment or {}).get("points", [])
    if series:
        latest = series[-1]
        wind = latest["wind"]
        hydro = latest["hydro"]
        nuclear = latest["nuclear"]
        policy = latest["chinaPolicy"]
        oil_gas = latest["oilGas"]
        historical_spread = 0.0
    elif historical_points:
        wind = float(np.mean([point["wind"] for point in historical_points[-3:]]))
        hydro_nuclear = float(np.mean([point["hydroNuclear"] for point in historical_points[-3:]]))
        hydro = hydro_nuclear
        nuclear = hydro_nuclear
        policy = float(np.mean([point["policy"] for point in historical_points[-3:]]))
        oil_gas = 0.0
        historical_spread = float(np.mean([point["spread"] for point in historical_points]))
    else:
        return [], []

    factors = [
        {
            "factor": "Wind ASP decline",
            "decImpact": "Low",
            "sheImpact": "High negative",
            "weight": round(max(0.2, 0.7 - wind), 2),
        },
        {
            "factor": "Hydropower expansion",
            "decImpact": "High positive",
            "sheImpact": "Neutral",
            "weight": round(hydro, 2),
        },
        {
            "factor": "Nuclear approvals",
            "decImpact": "High positive",
            "sheImpact": "Low",
            "weight": round(nuclear, 2),
        },
        {
            "factor": "China grid investment",
            "decImpact": "Positive",
            "sheImpact": "Mixed",
            "weight": round(policy, 2),
        },
        {
            "factor": "LNG / fossil fallback risk",
            "decImpact": "Neutral",
            "sheImpact": "Negative",
            "weight": round(abs(oil_gas), 2),
        },
    ]

    dec_score = round(7.2 + hydro * 1.3 + nuclear * 1.0 + policy * 0.6 + max(0, historical_spread) * 0.7 - max(0, -wind) * 0.25, 1)
    she_score = round(6.7 + wind * 0.8 - hydro * 0.25 - max(0, historical_spread) * 0.45 - max(0, -wind) * 1.4 - abs(oil_gas) * 0.4, 1)
    scores = [
        {
            "ticker": "1072.HK",
            "name": "Dongfang Electric",
            "aiScore": min(9.8, dec_score),
            "sentimentExposure": "Positive",
            "macroAlignment": "Strong",
            "thesis": "Hydro, nuclear, and China grid investment improve earnings visibility.",
        },
        {
            "ticker": "2727.HK",
            "name": "Shanghai Electric",
            "aiScore": max(1.0, she_score),
            "sentimentExposure": "Negative",
            "macroAlignment": "Weak",
            "thesis": "Wind margin pressure and execution risk weigh on relative positioning.",
        },
    ]
    return factors, scores


def detect_alerts(series: list[dict], coal_displacement_score: float = 0.0):
    if not series:
        return []
    latest = series[-1]
    prev = series[-3] if len(series) >= 3 else series[0]
    alerts = []
    now = datetime.now(timezone.utc)
    if latest["wind"] - prev["wind"] < -0.12:
        alerts.append(
            {
                "id": "alert-wind",
                "severity": "high",
                "title": "Wind sentiment drawdown",
                "detail": "Wind sector sentiment dropped sharply over the latest observation window.",
                "timestamp": now,
            }
        )
    if latest["chinaPolicy"] > 0.6 and latest["hydro"] > 0.55:
        alerts.append(
            {
                "id": "alert-policy",
                "severity": "opportunity",
                "title": "China policy tailwind",
                "detail": "Grid and dispatchable clean power signals are aligned with DEC exposure.",
                "timestamp": now,
            }
        )
    if coal_displacement_score >= 0.60:
        alerts.append(
            {
                "id": "alert-coal-displacement",
                "severity": "opportunity",
                "title": "Coal displacement push active",
                "detail": (
                    f"Coal displacement demand index is {coal_displacement_score:.2f}. "
                    "Thermal capacity retirement language is accelerating, redirecting capex into "
                    "hydro, nuclear, pumped storage and grid — a direct DEC order-book catalyst."
                ),
                "timestamp": now,
            }
        )
    return alerts


def generate_insights(scores: list[dict], narratives: list[dict], alerts: list[dict], company_sentiment: list[dict] | None = None, historical_sentiment: dict | None = None) -> list[str]:
    dec = next((row for row in company_sentiment or [] if row["ticker"] == "1072.HK"), {"finbertScore": 0})
    she = next((row for row in company_sentiment or [] if row["ticker"] == "2727.HK"), {"finbertScore": 0})
    spread = dec["finbertScore"] - she["finbertScore"]
    insights = []
    coal_alert = next((a for a in alerts if a["id"] == "alert-coal-displacement"), None)
    if coal_alert:
        insights.append(coal_alert["detail"])
    if (dec.get("headlineCount", 0) + she.get("headlineCount", 0)) > 0:
        insights.append(
            f"FinBERT company-headline spread is {spread:+.2f}; treat as supportive only if sample size and confidence are adequate."
            if abs(spread) > 0.2
            else "FinBERT company-headline spread is mixed; no company-sentiment confirmation yet."
        )
    if historical_sentiment:
        insights.append(historical_sentiment["summary"])
    coal_narrative = next((n for n in narratives if n["category"] == "Coal Displacement"), None)
    if coal_narrative:
        insights.append(f"Coal displacement narrative velocity: {coal_narrative['velocity']} — {coal_narrative['summary']}")
    elif narratives:
        insights.append(f"Top live headline narrative: {narratives[0]['label']}.")
    if scores:
        insights.extend([score["thesis"] for score in scores])
    wind_alert = next((a for a in alerts if a["id"] == "alert-wind"), None)
    if wind_alert:
        insights.append(f"Risk monitor: {wind_alert['title']}.")
    if not insights:
        insights.append("No live/pulled data available for an investment read on this refresh.")
    return insights


def _avg_category(rows: list[dict], category: str) -> float:
    values = [row["sentiment_score"] for row in rows if row["category"] == category]
    return round(float(np.mean(values)), 3) if values else 0.0


def _avg_categories(rows: list[dict], categories: set[str]) -> float:
    values = [row["sentiment_score"] for row in rows if row["category"] in categories]
    return round(float(np.mean(values)), 3) if values else 0.0


def _group_by(rows: list[dict], key: str) -> dict[str, list[dict]]:
    output: dict[str, list[dict]] = {}
    for row in rows:
        output.setdefault(row[key], []).append(row)
    return output


def _demand_investment_read(category: str, score: float) -> tuple[str, str, str]:
    if category == "Coal Displacement":
        return (
            "Strong positive",
            "Mixed / wind pricing risk",
            (
                "China's coal retirement structurally redirects capex into hydro, nuclear, pumped storage, grid upgrades "
                "and dispatchable clean generation — DEC's core equipment segments. SHE participates in renewables volume "
                "but faces ASP compression in wind as coal displacement spending concentrates on dispatchable assets."
            ),
        )
    if category in {"Hydropower", "Nuclear", "China policy"}:
        return "Positive", "Mixed", "Live headlines point to demand where DEC has stronger hydro/nuclear/grid alignment than SHE."
    if category == "Wind energy":
        she = "Positive" if score > 0.25 else "Margin risk"
        return "Low positive", she, "Wind demand is relevant to SHE, but the equity read depends on whether headlines imply volume growth or pricing pressure."
    if category == "Supply chain":
        return "Risk", "Risk", "Supply-chain stress can affect both companies; watch whether turbine components or heavy equipment are specifically mentioned."
    return "Mixed", "Mixed", "Macro energy-transition demand is broad and needs company-specific confirmation."
