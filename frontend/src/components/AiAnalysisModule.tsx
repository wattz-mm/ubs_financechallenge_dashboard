import { Bot, ChartNoAxesCombined, Scale, TableProperties } from "lucide-react";
import type { AiLayer } from "../types";

const icons = {
  "nlp-sentiment": TableProperties,
  "coal-displacement": ChartNoAxesCombined,
  "factor-screening": Scale
};

export function AiAnalysisModule({ layers }: { layers: AiLayer[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-5 shadow-sm">
      <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
        <div>
          <h2 className="text-xl font-semibold">AI-Assisted Analysis Module</h2>
          <p className="mt-1 text-sm text-slate-500">Three independent AI layers converge on the DEC/SHE long-short signal.</p>
        </div>
        <div className="inline-flex items-center gap-2 rounded-md bg-emerald-50 px-3 py-2 text-sm font-semibold text-emerald-700">
          <Bot size={17} />
          LONG DEC / SHORT SHE
        </div>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        {layers.map((layer) => {
          const Icon = icons[layer.id as keyof typeof icons] ?? Bot;
          return (
            <article key={layer.id} className="rounded-md border border-slate-200 bg-slate-50">
              <div className={`h-2 rounded-t-md ${barClass(layer.tone)}`} />
              <div className="p-4">
                <div className={`mb-3 inline-flex items-center gap-2 text-base font-semibold ${textClass(layer.tone)}`}>
                  <Icon size={22} />
                  {layer.title}
                </div>
                <p className="text-sm leading-6 text-slate-600"><span className="font-semibold text-ink">AI Method:</span> {layer.method}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600"><span className="font-semibold text-ink">Data:</span> {layer.data}</p>
                <p className="mt-2 text-sm leading-6 text-slate-600"><span className="font-semibold text-ink">Output:</span> {layer.output}</p>
              </div>
            </article>
          );
        })}
      </div>
      <div className="mt-4 grid grid-cols-1 items-center gap-3 md:grid-cols-[1fr_auto_1fr_auto_1fr]">
        <FlowBox tone="teal" title="Data Sources" lines={["GDELT headlines", "HK/China tickers", "China energy policy tape"]} />
        <span className="hidden text-3xl text-slate-400 md:block">→</span>
        <FlowBox tone="orange" title="AI Processing" lines={["FinBERT scoring", "Coal displacement proxy", "Factor screening"]} />
        <span className="hidden text-3xl text-slate-400 md:block">→</span>
        <FlowBox tone="green" title="Investment Signal" lines={["LONG DEC (1072.HK)", "SHORT SHE (2727.HK)"]} />
      </div>
    </section>
  );
}

function FlowBox({ tone, title, lines }: { tone: string; title: string; lines: string[] }) {
  return (
    <div className={`rounded-md px-4 py-4 text-white ${tone === "teal" ? "bg-teal-700" : tone === "orange" ? "bg-orange-600" : "bg-emerald-600"}`}>
      <p className="text-sm font-semibold uppercase">{title}</p>
      <div className="mt-3 space-y-1 text-sm">
        {lines.map((line) => <p key={line}>{line}</p>)}
      </div>
    </div>
  );
}

function barClass(tone: string) {
  if (tone === "orange") return "bg-orange-600";
  if (tone === "navy") return "bg-slate-800";
  return "bg-teal-700";
}

function textClass(tone: string) {
  if (tone === "orange") return "text-orange-700";
  if (tone === "navy") return "text-slate-800";
  return "text-teal-700";
}
