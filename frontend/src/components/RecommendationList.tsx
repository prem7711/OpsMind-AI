import type { Recommendation } from "../types";
import { Card, CardHeader } from "./Card";

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? "bg-emerald-500" : pct >= 45 ? "bg-amber-500" : "bg-rose-500";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-20 overflow-hidden rounded-full bg-white/10">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs tabular-nums text-slate-400">{pct}%</span>
    </div>
  );
}

export function RecommendationList({ recommendations }: { recommendations: Recommendation[] }) {
  if (recommendations.length === 0) return null;
  const sorted = [...recommendations].sort((a, b) => b.confidence - a.confidence);
  return (
    <Card>
      <CardHeader title="Recommendations" subtitle={`${recommendations.length} suggested action(s)`} />
      <div className="space-y-3">
        {sorted.map((rec, i) => (
          <div key={i} className="rounded-xl border border-white/10 bg-white/[0.02] p-4">
            <div className="mb-1.5 flex items-center justify-between gap-3">
              <div className="flex items-center gap-2">
                <span className="rounded-md bg-violet-500/10 px-2 py-0.5 text-[11px] font-medium uppercase tracking-wide text-violet-300 ring-1 ring-inset ring-violet-500/20">
                  {rec.category}
                </span>
                <span className="text-sm font-medium text-slate-100">{rec.action}</span>
              </div>
              <ConfidenceBar value={rec.confidence} />
            </div>
            <p className="text-sm text-slate-400">{rec.rationale}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
