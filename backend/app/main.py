import os
from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

IS_VERCEL = bool(os.environ.get("VERCEL"))

from .ai import (
    build_ai_layers,
    build_company_signals,
    build_data_freshness,
    build_energy_demand_signals_from_headlines,
    build_historical_sentiment_analysis,
    build_quant_metrics,
    build_regional_sentiment_from_headlines,
    build_sentiment_breakdown,
    build_sentiment_series_from_headlines,
    cluster_narratives,
    detect_alerts,
    finbert_company_sentiment,
    generate_insights,
    score_stock_screener,
)
from .config import settings
from .ingestion import IngestionService
from .models import DashboardPayload
from .sourced_data import sourced_energy_assets, sourced_energy_demand_signals, sourced_historical_sentiment_records, sourced_regional_sentiment

app = FastAPI(title=settings.app_name)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.cors_allow_all else settings.cors_origins,
    allow_credentials=not settings.cors_allow_all,
    allow_methods=["*"],
    allow_headers=["*"],
)

ingestion = IngestionService()
scheduler = AsyncIOScheduler()
cache: dict = {}


async def refresh_cache():
    headlines = await ingestion.fetch_headlines()
    company_headlines = await ingestion.fetch_company_headlines()
    raw_screener = await ingestion.fetch_stock_screener()
    sentiment_series = build_sentiment_series_from_headlines(headlines)
    sentiment_breakdown = build_sentiment_breakdown(headlines, sentiment_series)
    company_sentiment = finbert_company_sentiment(company_headlines)
    historical_sentiment = build_historical_sentiment_analysis(sourced_historical_sentiment_records(), company_sentiment)
    stock_screener = score_stock_screener(raw_screener, sentiment_breakdown)
    narratives = cluster_narratives(headlines)
    company_factors, company_scores = build_company_signals(sentiment_series, historical_sentiment)
    quant_metrics = build_quant_metrics(sentiment_series, headlines, stock_screener, company_sentiment)
    ai_layers = build_ai_layers(company_sentiment, quant_metrics, company_factors, historical_sentiment)
    coal_score = next((m["value"] for m in quant_metrics if m["metric"] == "Coal displacement demand push"), 0.0)
    alerts = detect_alerts(sentiment_series, coal_displacement_score=coal_score)
    insights = generate_insights(company_scores, narratives, alerts, company_sentiment, historical_sentiment)
    cache["dashboard"] = {
        "generatedAt": datetime.now(timezone.utc),
        "headlines": headlines,
        "sentimentSeries": sentiment_series,
        "sentimentBreakdown": sentiment_breakdown,
        "quantMetrics": quant_metrics,
        "regionalSentiment": build_regional_sentiment_from_headlines(headlines) or sourced_regional_sentiment(),
        "assets": sourced_energy_assets(),
        "narratives": narratives,
        "companyFactors": company_factors,
        "companyScores": company_scores,
        "companySentiment": company_sentiment,
        "historicalSentiment": historical_sentiment,
        "aiLayers": ai_layers,
        "energyDemandSignals": build_energy_demand_signals_from_headlines(headlines) or sourced_energy_demand_signals(),
        "dataFreshness": build_data_freshness(headlines, company_headlines, stock_screener),
        "stockScreener": stock_screener,
        "alerts": alerts,
        "insights": insights,
    }


def _build_sourced_cache():
    """Fast startup using sourced data only — no live HTTP. Used on Vercel."""
    company_headlines: dict[str, list] = {"1072.HK": [], "2727.HK": []}
    raw_screener = sourced_energy_assets()  # placeholder; screener uses sourced rows
    from .sourced_data import sourced_stock_rows
    raw_screener = sourced_stock_rows()
    sentiment_series: list = []
    sentiment_breakdown: list = []
    company_sentiment = finbert_company_sentiment(company_headlines)
    historical_sentiment = build_historical_sentiment_analysis(sourced_historical_sentiment_records(), company_sentiment)
    stock_screener = score_stock_screener(raw_screener, sentiment_breakdown)
    narratives: list = []
    company_factors, company_scores = build_company_signals(None, historical_sentiment)
    quant_metrics = build_quant_metrics(sentiment_series, [], stock_screener, company_sentiment)
    ai_layers = build_ai_layers(company_sentiment, quant_metrics, company_factors, historical_sentiment)
    coal_score = next((m["value"] for m in quant_metrics if m["metric"] == "Coal displacement demand push"), 0.0)
    alerts = detect_alerts(sentiment_series, coal_displacement_score=coal_score)
    insights = generate_insights(company_scores, narratives, alerts, company_sentiment, historical_sentiment)
    cache["dashboard"] = {
        "generatedAt": datetime.now(timezone.utc),
        "headlines": [],
        "sentimentSeries": sentiment_series,
        "sentimentBreakdown": sentiment_breakdown,
        "quantMetrics": quant_metrics,
        "regionalSentiment": sourced_regional_sentiment(),
        "assets": sourced_energy_assets(),
        "narratives": narratives,
        "companyFactors": company_factors,
        "companyScores": company_scores,
        "companySentiment": company_sentiment,
        "historicalSentiment": historical_sentiment,
        "aiLayers": ai_layers,
        "energyDemandSignals": sourced_energy_demand_signals(),
        "dataFreshness": build_data_freshness([], company_headlines, stock_screener),
        "stockScreener": stock_screener,
        "alerts": alerts,
        "insights": insights,
    }


@app.on_event("startup")
async def startup_event():
    if IS_VERCEL:
        _build_sourced_cache()
    else:
        await refresh_cache()
        scheduler.add_job(refresh_cache, "interval", hours=3, id="refresh-energy-intel", replace_existing=True)
        scheduler.start()


@app.on_event("shutdown")
async def shutdown_event():
    if not IS_VERCEL:
        scheduler.shutdown(wait=False)


@app.get("/health")
async def health():
    return {"status": "ok", "generatedAt": cache.get("dashboard", {}).get("generatedAt")}


@app.post("/api/ingest/run")
async def run_ingestion():
    await refresh_cache()
    return {"status": "refreshed", "generatedAt": cache["dashboard"]["generatedAt"]}


@app.get("/api/dashboard", response_model=DashboardPayload)
async def dashboard():
    if "dashboard" not in cache:
        await refresh_cache()
    return cache["dashboard"]


@app.get("/api/news")
async def news():
    if "dashboard" not in cache:
        await refresh_cache()
    return cache["dashboard"]["headlines"]


@app.get("/api/sentiment")
async def sentiment():
    if "dashboard" not in cache:
        await refresh_cache()
    return {
        "series": cache["dashboard"]["sentimentSeries"],
        "regions": cache["dashboard"]["regionalSentiment"],
        "narratives": cache["dashboard"]["narratives"],
        "breakdown": cache["dashboard"]["sentimentBreakdown"],
    }


@app.get("/api/company-signals")
async def company_signals():
    if "dashboard" not in cache:
        await refresh_cache()
    return {
        "factors": cache["dashboard"]["companyFactors"],
        "scores": cache["dashboard"]["companyScores"],
        "sentiment": cache["dashboard"]["companySentiment"],
        "screener": cache["dashboard"]["stockScreener"],
    }


@app.get("/api/screener")
async def screener():
    if "dashboard" not in cache:
        await refresh_cache()
    return cache["dashboard"]["stockScreener"]


@app.get("/api/export/ppt-ready")
async def ppt_ready_export():
    if "dashboard" not in cache:
        await refresh_cache()
    data = cache["dashboard"]
    return {
        "title": "Energy Intelligence: Long Dongfang Electric / Short Shanghai Electric",
        "generatedAt": data["generatedAt"],
        "slides": [
            {
                "title": "Macro Signal Dashboard",
                "commentary": data["insights"][:3],
                "charts": ["companySentiment", "historicalSentiment", "aiLayers", "sentimentBreakdown", "regionalSentiment"],
            },
            {
                "title": "Company Impact Scorecard",
                "commentary": [item["read"] for item in data["companySentiment"]],
                "charts": ["companyFactors", "companyScores", "stockScreener"],
            },
            {
                "title": "10-Year Source-Backed Sentiment Read",
                "commentary": [data["historicalSentiment"]["summary"], data["historicalSentiment"]["method"]],
                "charts": ["historicalSentiment"],
            },
            {
                "title": "Narrative Velocity and Risks",
                "commentary": [n["summary"] for n in data["narratives"][:5]],
                "charts": ["narratives", "alerts"],
            },
        ],
    }
