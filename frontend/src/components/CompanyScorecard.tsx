import type { CompanyFactor, CompanyScore } from "../types";

export function CompanyScorecard({ scores, factors }: { scores: CompanyScore[]; factors: CompanyFactor[] }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-base font-semibold">Company Signal Engine</h2>
        <span className="text-xs font-medium text-slate-500">Macro to alpha</span>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {scores.map((score) => (
          <div key={score.ticker} className="rounded-md border border-line p-3">
            <div className="flex items-start justify-between gap-2">
              <div>
                <p className="text-sm font-semibold">{score.name}</p>
                <p className="text-xs text-slate-500">{score.ticker}</p>
              </div>
              <div className={`rounded-md px-2 py-1 text-lg font-semibold ${score.aiScore >= 7 ? "bg-emerald-50 text-emerald-700" : "bg-orange-50 text-orange-700"}`}>{score.aiScore.toFixed(1)}</div>
            </div>
            <dl className="mt-3 space-y-1 text-xs">
              <Row label="Sentiment" value={score.sentimentExposure} />
              <Row label="Alignment" value={score.macroAlignment} />
            </dl>
            <p className="mt-3 text-xs leading-5 text-slate-600">{score.thesis}</p>
          </div>
        ))}
      </div>
      <table className="mt-4 w-full border-collapse text-left text-xs">
        <thead>
          <tr className="border-b border-line text-slate-500">
            <th className="py-2 font-medium">Factor</th>
            <th className="py-2 font-medium">DEC Impact</th>
            <th className="py-2 font-medium">SHE Impact</th>
            <th className="py-2 text-right font-medium">Weight</th>
          </tr>
        </thead>
        <tbody>
          {factors.map((factor) => (
            <tr key={factor.factor} className="border-b border-slate-100">
              <td className="py-2 font-medium">{factor.factor}</td>
              <td className="py-2 text-emerald-700">{factor.decImpact}</td>
              <td className="py-2 text-orange-700">{factor.sheImpact}</td>
              <td className="py-2 text-right">{factor.weight.toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between gap-2">
      <dt className="text-slate-500">{label}</dt>
      <dd className="font-medium">{value}</dd>
    </div>
  );
}

