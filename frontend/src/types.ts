export type Headline = {
  id: string;
  title: string;
  source: string;
  url?: string | null;
  published_at: string;
  region: string;
  category: string;
  sentiment: "bullish" | "neutral" | "bearish";
  sentiment_score: number;
  summary: string;
};

export type SentimentPoint = {
  timestamp: string;
  wind: number;
  hydro: number;
  nuclear: number;
  oilGas: number;
  chinaPolicy: number;
};

export type RegionSentiment = {
  region: string;
  coordinates: [number, number];
  renewables: number;
  chinaPolicy: number;
  supplyChain: number;
  demandIntensity: number;
};

export type EnergyAsset = {
  id: string;
  name: string;
  type: "hydro" | "nuclear" | "wind" | "oil_gas";
  region: string;
  coordinates: [number, number];
  capacityGw: number;
  status: string;
};

export type Narrative = {
  id: string;
  label: string;
  category: string;
  velocity: string;
  velocityScore: number;
  sentiment: string;
  summary: string;
  headlines: string[];
};

export type CompanyFactor = {
  factor: string;
  decImpact: string;
  sheImpact: string;
  weight: number;
};

export type CompanyScore = {
  ticker: string;
  name: string;
  aiScore: number;
  sentimentExposure: string;
  macroAlignment: string;
  thesis: string;
};

export type Alert = {
  id: string;
  severity: string;
  title: string;
  detail: string;
  timestamp: string;
};

export type SentimentBreakdown = {
  category: string;
  score: number;
  momentum48h: number;
  breadth: number;
  volume: number;
  confidence: number;
  dispersion: number;
  bullish: number;
  neutral: number;
  bearish: number;
  topTerms: string[];
  read: string;
};

export type QuantMetric = {
  metric: string;
  value: number | string;
  unit: string;
  signal: string;
  interpretation: string;
};

export type StockScreenerRow = {
  ticker: string;
  name: string;
  segment: string;
  price: number | null;
  changePct: number;
  momentum5d: number;
  volume?: number | null;
  asOf?: string | null;
  dataSource?: string | null;
  sourceUrl?: string | null;
  marketCap?: number | null;
  trailingPe?: number | null;
  forwardPe?: number | null;
  priceToBook?: number | null;
  dividendYield?: number | null;
  beta?: number | null;
  sentimentScore: number;
  aiScore: number;
  signal: string;
  read: string;
};

export type CompanySentiment = {
  ticker: string;
  name: string;
  headlineCount: number;
  finbertScore: number;
  finbertLabel: string;
  confidence: number;
  positive: number;
  neutral: number;
  negative: number;
  topTerms: string[];
  read: string;
  headlines: Headline[];
};

export type HistoricalSentimentPoint = {
  year: number;
  dec: number;
  she: number;
  spread: number;
  hydroNuclear: number;
  wind: number;
  policy: number;
  evidenceCount: number;
};

export type HistoricalSentimentEvidence = {
  year: number;
  company: string;
  category: string;
  title: string;
  source: string;
  sourceUrl: string;
  sentimentScore: number;
  read: string;
};

export type HistoricalSourceCoverage = {
  source: string;
  count: number;
  latestYear: number;
  use: string;
};

export type HistoricalSentimentAnalysis = {
  method: string;
  summary: string;
  points: HistoricalSentimentPoint[];
  evidence: HistoricalSentimentEvidence[];
  sourceCoverage: HistoricalSourceCoverage[];
};

export type AiLayer = {
  id: string;
  title: string;
  method: string;
  data: string;
  output: string;
  score: number;
  tone: "teal" | "orange" | "navy" | string;
};

export type EnergyDemandSignal = {
  region: string;
  coordinates: [number, number];
  demandType: string;
  demandScore: number;
  source: string;
  sourceUrl: string;
  evidence: string;
  decImpact: string;
  sheImpact: string;
  investmentRead: string;
};

export type DataFreshness = {
  layer: string;
  status: string;
  source: string;
  note: string;
};

export type DashboardPayload = {
  generatedAt: string;
  headlines: Headline[];
  sentimentSeries: SentimentPoint[];
  sentimentBreakdown: SentimentBreakdown[];
  quantMetrics: QuantMetric[];
  regionalSentiment: RegionSentiment[];
  assets: EnergyAsset[];
  narratives: Narrative[];
  companyFactors: CompanyFactor[];
  companyScores: CompanyScore[];
  companySentiment: CompanySentiment[];
  historicalSentiment: HistoricalSentimentAnalysis;
  aiLayers: AiLayer[];
  energyDemandSignals: EnergyDemandSignal[];
  dataFreshness: DataFreshness[];
  stockScreener: StockScreenerRow[];
  alerts: Alert[];
  insights: string[];
};
