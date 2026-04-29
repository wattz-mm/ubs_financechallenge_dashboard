import { AlertTriangle, Brain } from "lucide-react";
import type { Alert } from "../types";

export function InsightFeed({ insights, alerts, generatedAt }: { insights: string[]; alerts: Alert[]; generatedAt: string }) {
  return (
    <section className="rounded-md border border-line bg-white p-4 shadow-sm">
      <div className="mb-3 flex items-center justify-between">
        <h2 className="inline-flex items-center gap-2 text-base font-semibold"><Brain size={18} /> AI Insights Feed</h2>
        <span className="text-xs text-slate-500">{new Date(generatedAt).toLocaleTimeString()}</span>
      </div>
      <div className="space-y-2">
        {insights.map((insight) => (
          <div key={insight} className="rounded-md border border-slate-200 bg-slate-50 px-3 py-2 text-sm leading-6">{insight}</div>
        ))}
      </div>
      <div className="mt-4 space-y-2">
        {alerts.map((alert) => (
          <div key={alert.id} className={`rounded-md border px-3 py-2 ${alert.severity === "high" ? "border-red-200 bg-red-50" : alert.severity === "opportunity" ? "border-emerald-200 bg-emerald-50" : "border-orange-200 bg-orange-50"}`}>
            <div className="flex items-center gap-2 text-sm font-semibold">
              <AlertTriangle size={15} />
              {alert.title}
            </div>
            <p className="mt-1 text-xs leading-5 text-slate-600">{alert.detail}</p>
          </div>
        ))}
      </div>
    </section>
  );
}

