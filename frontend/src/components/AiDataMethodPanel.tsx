import { Brain, Database, Radio } from "lucide-react";
import type { AiLayer, DataFreshness } from "../types";

export function AiDataMethodPanel({ aiLayers, dataFreshness }: { aiLayers: AiLayer[]; dataFreshness: DataFreshness[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
        <div>
          <h2 className="inline-flex items-center gap-2 text-base font-semibold"><Brain size={18} /> AI + Data Method</h2>
          <p className="mt-1 text-xs leading-5 text-slate-500">How the dashboard turns news, prices and sourced infrastructure into the DEC/SHE read.</p>
        </div>
        <span className="inline-flex items-center gap-1.5 rounded bg-slate-100 px-2 py-1 text-xs font-medium text-slate-700"><Radio size={13} /> live + sourced</span>
      </div>
      <div className="grid grid-cols-1 gap-3 lg:grid-cols-[1.05fr_0.95fr]">
        <div className="space-y-2">
          {aiLayers.map((layer) => (
            <article key={layer.id} className="rounded-md border border-slate-200 p-3">
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-semibold">{layer.title}</p>
                  <p className="mt-1 text-xs leading-5 text-slate-600">{layer.method}</p>
                </div>
                <p className="text-lg font-semibold text-slate-800">{layer.score.toFixed(2)}</p>
              </div>
              <p className="mt-2 text-xs leading-5 text-slate-500">{layer.data}</p>
              <p className="mt-2 rounded bg-slate-50 px-2 py-1 text-xs font-medium text-slate-700">{layer.output}</p>
            </article>
          ))}
        </div>
        <div className="space-y-2">
          {dataFreshness.map((row) => (
            <article key={row.layer} className="rounded-md border border-slate-200 p-3">
              <div className="flex items-center justify-between gap-2">
                <p className="inline-flex items-center gap-2 text-sm font-semibold"><Database size={15} /> {row.layer}</p>
                <span className={`rounded px-2 py-0.5 text-[11px] font-semibold ${tone(row.status)}`}>{row.status}</span>
              </div>
              <p className="mt-1 text-xs text-slate-500">{row.source}</p>
              <p className="mt-2 text-xs leading-5 text-slate-600">{row.note}</p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}

function tone(status: string) {
  if (status.includes("Live attempt")) return "bg-blue-50 text-blue-700";
  if (status === "Live") return "bg-emerald-50 text-emerald-700";
  return "bg-slate-100 text-slate-600";
}
