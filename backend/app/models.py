from datetime import datetime
from pydantic import BaseModel, Field


class Headline(BaseModel):
    id: str
    title: str
    source: str
    url: str | None = None
    published_at: datetime
    region: str
    category: str
    sentiment: str
    sentiment_score: float
    summary: str


class SentimentPoint(BaseModel):
    timestamp: datetime
    wind: float
    hydro: float
    nuclear: float
    oil_gas: float = Field(alias="oilGas")
    china_policy: float = Field(alias="chinaPolicy")


class RegionSentiment(BaseModel):
    region: str
    coordinates: tuple[float, float]
    renewables: float
    china_policy: float = Field(alias="chinaPolicy")
    supply_chain: float = Field(alias="supplyChain")
    demand_intensity: float = Field(alias="demandIntensity")


class EnergyAsset(BaseModel):
    id: str
    name: str
    type: str
    region: str
    coordinates: tuple[float, float]
    capacity_gw: float = Field(alias="capacityGw")
    status: str
    source: str | None = None


class Narrative(BaseModel):
    id: str
    label: str
    category: str
    velocity: str
    velocity_score: float = Field(alias="velocityScore")
    sentiment: str
    summary: str
    headlines: list[str]


class CompanyFactor(BaseModel):
    factor: str
    dec_impact: str = Field(alias="decImpact")
    she_impact: str = Field(alias="sheImpact")
    weight: float


class CompanyScore(BaseModel):
    ticker: str
    name: str
    ai_score: float = Field(alias="aiScore")
    sentiment_exposure: str = Field(alias="sentimentExposure")
    macro_alignment: str = Field(alias="macroAlignment")
    thesis: str


class Alert(BaseModel):
    id: str
    severity: str
    title: str
    detail: str
    timestamp: datetime


class SentimentBreakdown(BaseModel):
    category: str
    score: float
    momentum_48h: float = Field(alias="momentum48h")
    breadth: float
    volume: int
    confidence: float
    dispersion: float
    bullish: int
    neutral: int
    bearish: int
    top_terms: list[str] = Field(alias="topTerms")
    read: str


class QuantMetric(BaseModel):
    metric: str
    value: float | str
    unit: str
    signal: str
    interpretation: str


class StockScreenerRow(BaseModel):
    ticker: str
    name: str
    segment: str
    price: float | None
    change_pct: float = Field(alias="changePct")
    momentum_5d: float = Field(alias="momentum5d")
    volume: float | None = None
    as_of: str | None = Field(default=None, alias="asOf")
    data_source: str | None = Field(default=None, alias="dataSource")
    source_url: str | None = Field(default=None, alias="sourceUrl")
    market_cap: float | None = Field(default=None, alias="marketCap")
    trailing_pe: float | None = Field(default=None, alias="trailingPe")
    forward_pe: float | None = Field(default=None, alias="forwardPe")
    price_to_book: float | None = Field(default=None, alias="priceToBook")
    dividend_yield: float | None = Field(default=None, alias="dividendYield")
    beta: float | None = None
    sentiment_score: float = Field(alias="sentimentScore")
    ai_score: float = Field(alias="aiScore")
    signal: str
    read: str


class CompanySentiment(BaseModel):
    ticker: str
    name: str
    headline_count: int = Field(alias="headlineCount")
    finbert_score: float = Field(alias="finbertScore")
    finbert_label: str = Field(alias="finbertLabel")
    confidence: float
    positive: int
    neutral: int
    negative: int
    top_terms: list[str] = Field(alias="topTerms")
    read: str
    headlines: list[Headline]


class HistoricalSentimentPoint(BaseModel):
    year: int
    dec: float
    she: float
    spread: float
    hydro_nuclear: float = Field(alias="hydroNuclear")
    wind: float
    policy: float
    evidence_count: int = Field(alias="evidenceCount")


class HistoricalSentimentEvidence(BaseModel):
    year: int
    company: str
    category: str
    title: str
    source: str
    source_url: str = Field(alias="sourceUrl")
    sentiment_score: float = Field(alias="sentimentScore")
    read: str


class HistoricalSourceCoverage(BaseModel):
    source: str
    count: int
    latest_year: int = Field(alias="latestYear")
    use: str


class HistoricalSentimentAnalysis(BaseModel):
    method: str
    summary: str
    points: list[HistoricalSentimentPoint]
    evidence: list[HistoricalSentimentEvidence]
    source_coverage: list[HistoricalSourceCoverage] = Field(alias="sourceCoverage")


class AiLayer(BaseModel):
    id: str
    title: str
    method: str
    data: str
    output: str
    score: float
    tone: str


class EnergyDemandSignal(BaseModel):
    region: str
    coordinates: tuple[float, float]
    demand_type: str = Field(alias="demandType")
    demand_score: float = Field(alias="demandScore")
    source: str
    source_url: str = Field(alias="sourceUrl")
    evidence: str
    dec_impact: str = Field(alias="decImpact")
    she_impact: str = Field(alias="sheImpact")
    investment_read: str = Field(alias="investmentRead")


class DataFreshness(BaseModel):
    layer: str
    status: str
    source: str
    note: str


class DashboardPayload(BaseModel):
    generated_at: datetime = Field(alias="generatedAt")
    headlines: list[Headline]
    sentiment_series: list[SentimentPoint] = Field(alias="sentimentSeries")
    sentiment_breakdown: list[SentimentBreakdown] = Field(alias="sentimentBreakdown")
    quant_metrics: list[QuantMetric] = Field(alias="quantMetrics")
    regional_sentiment: list[RegionSentiment] = Field(alias="regionalSentiment")
    assets: list[EnergyAsset]
    narratives: list[Narrative]
    company_factors: list[CompanyFactor] = Field(alias="companyFactors")
    company_scores: list[CompanyScore] = Field(alias="companyScores")
    company_sentiment: list[CompanySentiment] = Field(alias="companySentiment")
    historical_sentiment: HistoricalSentimentAnalysis = Field(alias="historicalSentiment")
    ai_layers: list[AiLayer] = Field(alias="aiLayers")
    energy_demand_signals: list[EnergyDemandSignal] = Field(alias="energyDemandSignals")
    data_freshness: list[DataFreshness] = Field(alias="dataFreshness")
    stock_screener: list[StockScreenerRow] = Field(alias="stockScreener")
    alerts: list[Alert]
    insights: list[str]
