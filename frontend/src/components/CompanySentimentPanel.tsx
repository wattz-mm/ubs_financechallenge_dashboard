import type { CompanySentiment } from "../types";

export function CompanySentimentPanel({ rows }: { rows: CompanySentiment[] }) {
  const dec = rows.find((row) => row.ticker === "1072.HK");
  const she = rows.find((row) => row.ticker === "2727.HK");
  const spread = dec && she ? dec.finbertScore - she.finbertScore : 0;

  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">DEC vs SHE FinBERT Sentiment</h2>
        <span className={spread >= 0 ? "text-xs font-semibold text-emerald-700" : "text-xs font-semibold text-red-700"}>Spread {signed(spread)}</span>
      </div>
      <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
        {rows.map((row) => (
          <div key={row.ticker} className="rounded-md border border-slate-200 p-3">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-sm font-semibold">{row.name}</p>
                <p className="text-xs text-slate-500">{row.ticker} · {row.headlineCount} headlines</p>
              </div>
              <div className={row.finbertScore >= 0 ? "text-right text-emerald-700" : "text-right text-red-700"}>
                <p className="text-xl font-semibold">{signed(row.finbertScore)}</p>
                <p className="text-[11px] uppercase">{row.finbertLabel}</p>
              </div>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded bg-slate-100">
              <div className="h-full bg-emerald-500" style={{ width: `${pct(row.positive, row.headlineCount)}%` }} />
            </div>
            <div className="mt-2 flex justify-between text-[11px] text-slate-500">
              <span>{row.positive} pos</span>
              <span>{row.neutral} neutral</span>
              <span>{row.negative} neg</span>
              <span>{(row.confidence * 100).toFixed(0)}% conf</span>
            </div>
            <p className="mt-3 text-xs leading-5 text-slate-600">{row.read}</p>
            <div className="mt-2 flex flex-wrap gap-1">
              {row.topTerms.map((term) => (
                <span key={term} className="rounded bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600">{term}</span>
              ))}
            </div>
          </div>
        ))}
      </div>
      <div className="mt-4 border-t border-line pt-3">
        <p className="mb-2 text-xs font-semibold uppercase text-slate-500">Recent company headlines</p>
        <div className="space-y-2">
          {rows.flatMap((row) => row.headlines.slice(0, 3).map((headline) => ({ ...headline, owner: row.ticker }))).map((headline) => (
            <a key={`${headline.owner}-${headline.id}`} className="block text-xs leading-5 text-slate-700 hover:text-ink" href={headline.url ?? undefined} target="_blank" rel="noreferrer">
              <span className="font-semibold text-slate-500">{headline.owner}</span>
              {" · "}
              <span className={headline.sentiment === "bullish" ? "text-emerald-700" : headline.sentiment === "bearish" ? "text-red-700" : "text-slate-500"}>{headline.sentiment.toUpperCase()}</span>
              {"  "}{headline.title}
            </a>
          ))}
        </div>
      </div>
    </section>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function pct(part: number, total: number) {
  return total ? Math.max(4, Math.round((part / total) * 100)) : 0;
}
