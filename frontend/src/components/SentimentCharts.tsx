import { Area, AreaChart, CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { SentimentBreakdown, SentimentPoint } from "../types";

export function SentimentCharts({ series, breakdown }: { series: SentimentPoint[]; breakdown: SentimentBreakdown[] }) {
  const rows = series.map((point) => ({
    ...point,
    date: new Date(point.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })
  }));

  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">China Energy Sentiment Indices</h2>
        <span className="text-xs text-slate-500">Policy, hydro, nuclear, wind</span>
      </div>
      <div className="h-60">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={rows}>
            <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={18} />
            <YAxis domain={[-0.8, 0.9]} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line type="monotone" dataKey="wind" stroke="#3867d6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="hydro" stroke="#148f77" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="nuclear" stroke="#8b5cf6" strokeWidth={2} dot={false} />
            <Line type="monotone" dataKey="chinaPolicy" stroke="#dc2626" strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 h-28">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={rows}>
            <XAxis dataKey="date" hide />
            <YAxis hide domain={[0, 1]} />
            <Tooltip />
            <Area dataKey="hydro" stackId="1" stroke="#148f77" fill="#148f77" fillOpacity={0.32} />
            <Area dataKey="nuclear" stackId="1" stroke="#8b5cf6" fill="#8b5cf6" fillOpacity={0.25} />
          </AreaChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-2">
        {breakdown.slice(0, 4).map((item) => (
          <div key={item.category} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{item.category}</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">{item.read}</p>
              </div>
              <div className={item.score >= 0 ? "text-right text-emerald-700" : "text-right text-red-700"}>
                <p className="text-lg font-semibold">{item.score.toFixed(2)}</p>
                <p className="text-[11px]">conf {(item.confidence * 100).toFixed(0)}%</p>
              </div>
            </div>
            <div className="mt-3 grid grid-cols-4 gap-2 text-[11px] text-slate-600">
              <Mini label="Volume" value={item.volume.toString()} />
              <Mini label="Breadth" value={signed(item.breadth)} />
              <Mini label="48h" value={signed(item.momentum48h)} />
              <Mini label="Disp." value={item.dispersion.toFixed(2)} />
            </div>
            <div className="mt-2 flex flex-wrap gap-1">
              {item.topTerms.map((term) => (
                <span key={term} className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">{term}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
    </section>
  );
}

function Mini({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded bg-slate-50 px-2 py-1">
      <p className="text-slate-400">{label}</p>
      <p className="font-semibold text-slate-700">{value}</p>
    </div>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}
