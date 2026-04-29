import type { Headline, Narrative } from "../types";

export function NarrativePanel({ narratives, headlines }: { narratives: Narrative[]; headlines: Headline[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">Narrative Detection</h2>
        <span className="text-xs text-slate-500">Top 5 clusters</span>
      </div>
      <div className="space-y-2">
        {narratives.map((narrative) => (
          <div key={narrative.id} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-center justify-between gap-2">
              <p className="text-sm font-semibold">{narrative.label}</p>
              <span className={`rounded px-2 py-0.5 text-xs font-medium ${narrative.velocity === "growing" ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-600"}`}>{narrative.velocity}</span>
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-600">{narrative.summary}</p>
          </div>
        ))}
      </div>
      <div className="mt-4 border-t border-line pt-3">
        <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Latest headlines</p>
        <div className="space-y-2">
          {headlines.slice(0, 4).map((headline) => (
            <a key={headline.id} className="block text-xs leading-5 text-slate-700 hover:text-ink" href={headline.url ?? undefined} target="_blank" rel="noreferrer">
              <span className={headline.sentiment === "bullish" ? "text-emerald-700" : headline.sentiment === "bearish" ? "text-red-700" : "text-slate-500"}>{headline.sentiment.toUpperCase()}</span>
              {"  "}{headline.title}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

