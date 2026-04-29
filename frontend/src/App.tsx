import { useEffect, useMemo, useState } from "react";
import { Activity, AlertTriangle, Download, Layers, RefreshCw, TrendingDown, TrendingUp } from "lucide-react";
import type { DashboardPayload } from "./types";
import { fetchDashboard, fetchPptReady, refreshIngestion } from "./api";
import { EnergyMap } from "./components/EnergyMap";
import { SentimentCharts } from "./components/SentimentCharts";
import { CompanyScorecard } from "./components/CompanyScorecard";
import { InsightFeed } from "./components/InsightFeed";
import { NarrativePanel } from "./components/NarrativePanel";
import { QuantMetricsPanel } from "./components/QuantMetricsPanel";
import { StockScreener } from "./components/StockScreener";
import { CompanySentimentPanel } from "./components/CompanySentimentPanel";
import { ThesisOverview } from "./components/ThesisOverview";
import { EnergyDemandSignalsPanel } from "./components/EnergyDemandSignalsPanel";
import { DataFreshnessPanel } from "./components/DataFreshnessPanel";
import { AiDataMethodPanel } from "./components/AiDataMethodPanel";
import { HistoricalSentimentPanel } from "./components/HistoricalSentimentPanel";

const DEFAULT_LAYERS = {
  wind: true,
  hydro: true,
  nuclear: true,
  oilGas: true,
  demandSignals: true,
  renewablesSentiment: true,
  chinaPolicy: true,
  supplyChain: true
};

export default function App() {
  const [data, setData] = useState<DashboardPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [layers, setLayers] = useState(DEFAULT_LAYERS);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      setData(await fetchDashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown dashboard error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const id = window.setInterval(load, 10 * 60 * 1000);
    return () => window.clearInterval(id);
  }, []);

  const latest = data?.sentimentSeries.at(-1);
  const spread = useMemo(() => {
    if (!data) return null;
    const dec = data.companyScores.find((x) => x.name.includes("Dongfang"))?.aiScore ?? 0;
    const she = data.companyScores.find((x) => x.name.includes("Shanghai"))?.aiScore ?? 0;
    return (dec - she).toFixed(1);
  }, [data]);

  async function handleRefresh() {
    setLoading(true);
    await refreshIngestion();
    await load();
  }

  async function handleExport() {
    const payload = await fetchPptReady();
    const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "energy-intelligence-ppt-ready.json";
    anchor.click();
    URL.revokeObjectURL(url);
  }

  return (
    <main className="min-h-screen bg-[#e9eef4] text-ink">
      <header className="no-print border-b border-line bg-white/90 backdrop-blur">
        <div className="mx-auto flex max-w-[1800px] flex-wrap items-center justify-between gap-3 px-5 py-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">Energy Intelligence</p>
            <h1 className="text-2xl font-semibold tracking-normal">LONG Dongfang Electric / SHORT Shanghai Electric</h1>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Metric icon={<TrendingUp size={16} />} label="DEC-SHE spread" value={spread ? `+${spread}` : "--"} tone="green" />
            <Metric icon={<TrendingDown size={16} />} label="Wind sentiment" value={latest ? latest.wind.toFixed(2) : "--"} tone="blue" />
            <Metric icon={<Activity size={16} />} label="China policy" value={latest ? latest.chinaPolicy.toFixed(2) : "--"} tone="violet" />
            <button className="inline-flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 text-sm font-medium shadow-sm" onClick={handleRefresh} disabled={loading}>
              <RefreshCw size={16} className={loading ? "animate-spin" : ""} />
              Refresh
            </button>
            <button className="inline-flex h-10 items-center gap-2 rounded-md bg-ink px-3 text-sm font-medium text-white shadow-sm" onClick={handleExport}>
              <Download size={16} />
              Export
            </button>
          </div>
        </div>
      </header>

      {error && (
        <div className="mx-auto mt-4 flex max-w-[1800px] items-center gap-2 border border-red-200 bg-red-50 px-5 py-3 text-sm text-red-700">
          <AlertTriangle size={16} />
          {error}
        </div>
      )}

      {data ? (
        <div className="mx-auto max-w-[1800px] space-y-4 px-5 py-5">
          <ThesisOverview data={data} />
          <AiDataMethodPanel aiLayers={data.aiLayers ?? []} dataFreshness={data.dataFreshness ?? []} />
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-[minmax(760px,1.35fr)_minmax(520px,0.9fr)]">
            <section className="space-y-4">
              <div className="flex flex-wrap items-center gap-2 rounded-md border border-line bg-white p-3 shadow-sm">
                <span className="inline-flex items-center gap-2 text-sm font-semibold"><Layers size={16} /> Layers</span>
                {Object.keys(DEFAULT_LAYERS).map((key) => (
                  <button
                    key={key}
                    className={`h-8 rounded-md border px-2 text-xs font-medium ${layers[key as keyof typeof layers] ? "border-ink bg-ink text-white" : "border-line bg-white text-slate-600"}`}
                    onClick={() => setLayers((prev) => ({ ...prev, [key]: !prev[key as keyof typeof layers] }))}
                  >
                    {labelLayer(key)}
                  </button>
                ))}
              </div>
              <EnergyMap data={data} layers={layers} />
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <EnergyDemandSignalsPanel signals={data.energyDemandSignals ?? []} />
                <CompanySentimentPanel rows={data.companySentiment ?? []} />
              </div>
              <NarrativePanel narratives={data.narratives} headlines={data.headlines} />
              <HistoricalSentimentPanel analysis={data.historicalSentiment} />
              <StockScreener rows={data.stockScreener ?? []} />
            </section>
            <aside className="space-y-4">
              <InsightFeed insights={data.insights} alerts={data.alerts} generatedAt={data.generatedAt} />
              <DataFreshnessPanel rows={data.dataFreshness ?? []} />
              <SentimentCharts series={data.sentimentSeries} breakdown={data.sentimentBreakdown ?? []} />
              <QuantMetricsPanel metrics={data.quantMetrics ?? []} />
              <CompanyScorecard scores={data.companyScores} factors={data.companyFactors} />
            </aside>
          </div>
        </div>
      ) : (
        <div className="mx-auto max-w-[1800px] px-5 py-8 text-sm text-slate-600">Loading energy intelligence...</div>
      )}
    </main>
  );
}

function Metric({ icon, label, value, tone }: { icon: React.ReactNode; label: string; value: string; tone: "green" | "blue" | "violet" }) {
  const toneClass = tone === "green" ? "text-emerald-700" : tone === "blue" ? "text-blue-700" : "text-violet-700";
  return (
    <div className="flex h-10 items-center gap-2 rounded-md border border-line bg-white px-3 shadow-sm">
      <span className={toneClass}>{icon}</span>
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-sm font-semibold">{value}</span>
    </div>
  );
}

function labelLayer(key: string) {
  return key
    .replace("oilGas", "oil & gas")
    .replace("demandSignals", "demand signals")
    .replace("renewablesSentiment", "renewables sentiment")
    .replace("chinaPolicy", "China policy")
    .replace("supplyChain", "supply chain");
}
