import type { DataFreshness } from "../types";

export function DataFreshnessPanel({ rows }: { rows: DataFreshness[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3">
        <h2 className="text-base font-semibold">Map Data Status</h2>
        <p className="mt-1 text-xs leading-5 text-slate-500">What is live, what is sourced, and how to read the map.</p>
      </div>
      <div className="space-y-2">
        {rows.map((row) => (
          <div key={row.layer} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold">{row.layer}</p>
              <span className={`rounded px-2 py-0.5 text-[11px] font-semibold ${row.status === "Live" ? "bg-emerald-50 text-emerald-700" : row.status === "Live attempt" ? "bg-blue-50 text-blue-700" : "bg-slate-100 text-slate-600"}`}>{row.status}</span>
            </div>
            <p className="mt-1 text-xs text-slate-500">{row.source}</p>
            <p className="mt-2 text-xs leading-5 text-slate-600">{row.note}</p>
          </div>
        ))}
      </div>
    </section>
  );
}
