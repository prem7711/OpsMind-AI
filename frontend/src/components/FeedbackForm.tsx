import { useState } from "react";
import { Card, CardHeader } from "./Card";

export function FeedbackForm({
  incidentId,
  investigationId,
  onSubmit,
}: {
  incidentId: number;
  investigationId: number;
  onSubmit: (params: { incidentId: number; investigationId?: number; rating: number; comment: string }) => Promise<unknown>;
}) {
  const [rating, setRating] = useState(0);
  const [comment, setComment] = useState("");
  const [sent, setSent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function handleSubmit() {
    if (rating === 0) return;
    setBusy(true);
    try {
      await onSubmit({ incidentId, investigationId, rating, comment });
      setSent(true);
    } finally {
      setBusy(false);
    }
  }

  if (sent) {
    return (
      <Card>
        <p className="text-sm text-emerald-400">Thanks — feedback recorded.</p>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader title="Was this investigation helpful?" subtitle="Feedback improves future runs" />
      <div className="space-y-3">
        <div className="flex gap-1.5">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => setRating(n)}
              className={`h-8 w-8 rounded-lg text-sm font-medium ring-1 ring-inset transition-colors ${
                n <= rating
                  ? "bg-amber-500/20 text-amber-300 ring-amber-500/40"
                  : "bg-white/[0.02] text-slate-500 ring-white/10 hover:bg-white/5"
              }`}
            >
              {n}
            </button>
          ))}
        </div>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={2}
          placeholder="Optional comment..."
          className="w-full resize-none rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none ring-indigo-500/50 focus:ring-2"
        />
        <button
          onClick={handleSubmit}
          disabled={rating === 0 || busy}
          className="rounded-lg bg-white/10 px-4 py-2 text-sm font-medium text-slate-100 transition-colors hover:bg-white/15 disabled:opacity-40"
        >
          Submit feedback
        </button>
      </div>
    </Card>
  );
}
