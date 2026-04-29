import type { QuantMetric } from "../types";

export function QuantMetricsPanel({ metrics }: { metrics: QuantMetric[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">Quantitative Metrics</h2>
        <span className="text-xs text-slate-500">Investability checks</span>
      </div>
      <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-1">
        {metrics.length === 0 && <p className="text-sm text-slate-500">Waiting for quantitative metrics...</p>}
        {metrics.map((metric) => (
          <div key={metric.metric} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{metric.metric}</p>
                <p className="mt-1 text-xs leading-5 text-slate-600">{metric.interpretation}</p>
              </div>
              <div className="min-w-20 text-right">
                <p className="text-lg font-semibold">{typeof metric.value === "number" ? metric.value.toFixed(2) : metric.value}</p>
                <p className="text-[11px] text-slate-500">{metric.unit}</p>
              </div>
            </div>
            <p className="mt-2 inline-flex rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700">{metric.signal}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
