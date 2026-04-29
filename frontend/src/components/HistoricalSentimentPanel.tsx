import { Bar, CartesianGrid, ComposedChart, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { HistoricalSentimentAnalysis } from "../types";

export function HistoricalSentimentPanel({ analysis }: { analysis?: HistoricalSentimentAnalysis }) {
  if (!analysis) return null;

  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold">10-Year Source-Backed Sentiment</h2>
          <p className="mt-1 max-w-3xl text-xs leading-5 text-slate-500">{analysis.summary}</p>
        </div>
        <span className="rounded bg-emerald-50 px-2 py-1 text-xs font-semibold text-emerald-700">
          {analysis.points.reduce((sum, point) => sum + point.evidenceCount, 0)} evidence reads
        </span>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-[1.35fr_0.85fr]">
        <div className="rounded-md border border-slate-200 p-3">
          <div className="mb-2 flex items-center justify-between">
            <p className="text-sm font-semibold">DEC vs SHE Historical Sentiment Spread</p>
            <p className="text-xs text-slate-500">positive = supports long DEC / short SHE</p>
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <ComposedChart data={analysis.points}>
                <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
                <XAxis dataKey="year" tick={{ fontSize: 11 }} />
                <YAxis domain={[-0.8, 0.8]} tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="spread" fill="#0f766e" fillOpacity={0.22} name="DEC-SHE spread" />
                <Line type="monotone" dataKey="dec" stroke="#047857" strokeWidth={2} dot={false} name="DEC" />
                <Line type="monotone" dataKey="she" stroke="#dc2626" strokeWidth={2} dot={false} name="SHE" />
              </ComposedChart>
            </ResponsiveContainer>
          </div>
          <p className="mt-2 text-xs leading-5 text-slate-500">{analysis.method}</p>
        </div>

        <div className="rounded-md border border-slate-200 p-3">
          <p className="text-sm font-semibold">Source Coverage</p>
          <div className="mt-3 max-h-72 space-y-2 overflow-auto pr-1">
            {analysis.sourceCoverage.map((source) => (
              <div key={`${source.source}-${source.latestYear}`} className="rounded bg-slate-50 p-2">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold text-slate-800">{source.source}</p>
                  <span className="shrink-0 rounded bg-white px-1.5 py-0.5 text-[11px] text-slate-500">{source.count}x</span>
                </div>
                <p className="mt-1 text-[11px] leading-4 text-slate-500">{source.use} · latest {source.latestYear}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-1 gap-3 lg:grid-cols-2">
        {analysis.evidence.slice(0, 6).map((item) => (
          <a
            key={`${item.year}-${item.title}`}
            href={item.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="rounded-md border border-slate-200 p-3 transition hover:border-slate-300 hover:bg-slate-50"
          >
            <div className="flex items-center justify-between gap-2">
              <p className="text-xs font-semibold uppercase text-slate-500">{item.year} · {item.company} · {item.category}</p>
              <span className={item.sentimentScore >= 0 ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-red-700"}>
                {signed(item.sentimentScore)}
              </span>
            </div>
            <p className="mt-1 text-sm font-semibold text-slate-900">{item.title}</p>
            <p className="mt-1 text-xs leading-5 text-slate-600">{item.read}</p>
            <p className="mt-2 text-[11px] text-slate-400">{item.source}</p>
          </a>
        ))}
      </div>
    </section>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}
