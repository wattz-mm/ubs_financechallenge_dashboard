import { ArrowDownRight, ArrowUpRight, CheckCircle2 } from "lucide-react";
import type { DashboardPayload } from "../types";

export function ThesisOverview({ data }: { data: DashboardPayload }) {
  const dec = data.companySentiment?.find((row) => row.ticker === "1072.HK");
  const she = data.companySentiment?.find((row) => row.ticker === "2727.HK");
  const decScore = data.companyScores.find((row) => row.ticker === "1072.HK")?.aiScore;
  const sheScore = data.companyScores.find((row) => row.ticker === "2727.HK")?.aiScore;
  const decThesis = data.companyScores.find((row) => row.ticker === "1072.HK")?.thesis;
  const sheThesis = data.companyScores.find((row) => row.ticker === "2727.HK")?.thesis;
  const liveSpread = dec && she ? dec.finbertScore - she.finbertScore : 0;
  const historicalSpread = data.historicalSentiment?.points.length
    ? data.historicalSentiment.points.reduce((sum, point) => sum + point.spread, 0) / data.historicalSentiment.points.length
    : 0;
  const hasLiveCompanyData = Boolean((dec?.headlineCount ?? 0) + (she?.headlineCount ?? 0));
  const spread = hasLiveCompanyData ? liveSpread : historicalSpread;

  return (
    <section className="rounded-md border border-line bg-white p-5 shadow-sm">
      <div className="mb-4">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-slate-500">Overall Read</p>
        <h2 className="mt-1 text-xl font-semibold">Why Long Dongfang Electric / Short Shanghai Electric</h2>
      </div>
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-3">
        <div className="rounded-md border border-emerald-200 bg-emerald-50 p-4">
          <div className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-emerald-700">
            <ArrowUpRight size={18} />
            Long DEC
          </div>
          <p className="text-2xl font-semibold text-emerald-800">{decScore !== undefined ? decScore.toFixed(1) : "--"}</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{dec?.headlineCount ? dec.read : decThesis ?? "No DEC signal available on this refresh."}</p>
        </div>
        <div className="rounded-md border border-red-200 bg-red-50 p-4">
          <div className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-red-700">
            <ArrowDownRight size={18} />
            Short SHE
          </div>
          <p className="text-2xl font-semibold text-red-800">{sheScore !== undefined ? sheScore.toFixed(1) : "--"}</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">{she?.headlineCount ? she.read : sheThesis ?? "No SHE signal available on this refresh."}</p>
        </div>
        <div className="rounded-md border border-slate-200 bg-slate-50 p-4">
          <div className="mb-2 inline-flex items-center gap-2 text-sm font-semibold text-slate-700">
            <CheckCircle2 size={18} />
            Confirmation
          </div>
          <p className={spread >= 0 ? "text-2xl font-semibold text-emerald-700" : "text-2xl font-semibold text-red-700"}>{signed(spread)}</p>
          <p className="mt-2 text-sm leading-6 text-slate-700">
            {hasLiveCompanyData ? "DEC less SHE FinBERT headline spread from recent company news." : "DEC less SHE 10-year sourced sentiment spread, used because live company headlines are thin."}
          </p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-1 gap-3 md:grid-cols-3">
        {data.insights.slice(0, 3).map((insight) => (
          <p key={insight} className="rounded-md border border-slate-200 px-3 py-2 text-sm leading-6 text-slate-700">{insight}</p>
        ))}
      </div>
    </section>
  );
}

function signed(value: number) {
  return `${value > 0 ? "+" : ""}${value.toFixed(2)}`;
}
