import type { StockScreenerRow } from "../types";

export function StockScreener({ rows }: { rows: StockScreenerRow[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">China Energy Transition Screener</h2>
        <span className="text-xs text-slate-500">Online quotes + sourced universe</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[980px] border-collapse text-left text-xs">
          <thead>
            <tr className="border-b border-line text-slate-500">
              <th className="py-2 font-medium">Company</th>
              <th className="py-2 font-medium">Segment</th>
              <th className="py-2 text-right font-medium">Price</th>
              <th className="py-2 text-right font-medium">1D</th>
              <th className="py-2 text-right font-medium">5D</th>
              <th className="py-2 text-right font-medium">Volume</th>
              <th className="py-2 text-right font-medium">Sent.</th>
              <th className="py-2 text-right font-medium">AI</th>
              <th className="py-2 font-medium">Source</th>
              <th className="py-2 font-medium">Signal</th>
            </tr>
          </thead>
          <tbody>
            {rows.length === 0 && (
              <tr>
                <td className="py-4 text-slate-500" colSpan={10}>Waiting for screener data...</td>
              </tr>
            )}
            {rows.map((row) => (
              <tr key={row.ticker} className="border-b border-slate-100 align-top">
                <td className="py-2">
                  <p className="font-semibold">{row.name}</p>
                  <p className="text-slate-500">{row.ticker}</p>
                </td>
                <td className="py-2 text-slate-600">{row.segment}</td>
                <td className="py-2 text-right">{row.price?.toFixed(2) ?? "--"}</td>
                <td className={tone(row.changePct)}>{signed(row.changePct)}%</td>
                <td className={tone(row.momentum5d)}>{signed(row.momentum5d)}%</td>
                <td className="py-2 text-right">{row.volume ? compact(row.volume) : "--"}</td>
                <td className={tone(row.sentimentScore)}>{signed(row.sentimentScore)}</td>
                <td className="py-2 text-right font-semibold">{row.aiScore.toFixed(1)}</td>
                <td className="py-2 text-slate-500">
                  {row.sourceUrl ? <a className="hover:text-ink" href={row.sourceUrl} target="_blank" rel="noreferrer">{row.dataSource ?? "Online"}</a> : row.dataSource ?? "--"}
                  {row.asOf && <p className="mt-1 text-[11px]">{row.asOf}</p>}
                </td>
                <td className="py-2">
                  <span className={`rounded px-2 py-1 font-medium ${row.signal === "Long candidate" ? "bg-emerald-50 text-emerald-700" : row.signal === "Short watch" ? "bg-red-50 text-red-700" : "bg-slate-100 text-slate-600"}`}>{row.signal}</span>
                  <p className="mt-2 max-w-[240px] leading-5 text-slate-500">{row.read}</p>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}

function tone(value: number) {
  return `py-2 text-right ${value > 0 ? "text-emerald-700" : value < 0 ? "text-red-700" : "text-slate-600"}`;
}

function compact(value: number) {
  return new Intl.NumberFormat(undefined, { notation: "compact", maximumFractionDigits: 1 }).format(value);
}
