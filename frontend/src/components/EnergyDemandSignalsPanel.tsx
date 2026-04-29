import type { EnergyDemandSignal } from "../types";

export function EnergyDemandSignalsPanel({ signals }: { signals: EnergyDemandSignal[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">China Energy Demand Signals</h2>
        <span className="text-xs text-slate-500">{signals.length} sourced regional reads</span>
      </div>
      <div className="space-y-3">
        {signals.map((signal) => (
          <article key={`${signal.region}-${signal.demandType}`} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{signal.region}</p>
                <p className="text-xs text-slate-500">{signal.demandType}</p>
              </div>
              <div className="text-right">
                <p className="text-lg font-semibold text-slate-800">{signal.demandScore.toFixed(2)}</p>
                <p className="text-[11px] text-slate-500">demand score</p>
              </div>
            </div>
            <p className="mt-2 text-xs leading-5 text-slate-600">{signal.evidence}</p>
            <p className="mt-2 text-xs leading-5 font-medium text-slate-700">{signal.investmentRead}</p>
            <div className="mt-3 flex flex-wrap items-center gap-2 text-[11px]">
              <span className="rounded bg-emerald-50 px-2 py-1 font-medium text-emerald-700">DEC: {signal.decImpact}</span>
              <span className="rounded bg-orange-50 px-2 py-1 font-medium text-orange-700">SHE: {signal.sheImpact}</span>
              <a className="rounded bg-slate-100 px-2 py-1 font-medium text-slate-600 hover:text-ink" href={signal.sourceUrl} target="_blank" rel="noreferrer">{signal.source}</a>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
