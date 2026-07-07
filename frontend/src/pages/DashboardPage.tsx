import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getDashboard } from "../api/client";
import { Card, CardHeader } from "../components/Card";
import { StatusBadge } from "../components/Badge";
import { Spinner } from "../components/Spinner";
import type { DashboardData } from "../types";

const SEVERITY_ORDER = ["critical", "high", "medium", "low"];
const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-rose-500",
  high: "bg-orange-500",
  medium: "bg-amber-500",
  low: "bg-emerald-500",
};

function StatTile({ label, value }: { label: string; value: string | number }) {
  return (
    <Card>
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className="mt-1.5 text-3xl font-semibold text-slate-100">{value}</p>
    </Card>
  );
}

export function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch((err) => setError(err instanceof Error ? err.message : "failed to load dashboard"));
  }, []);

  if (error) return <div className="mx-auto max-w-5xl px-6 py-10 text-sm text-rose-400">{error}</div>;
  if (!data) {
    return (
      <div className="mx-auto flex max-w-5xl items-center gap-2 px-6 py-10 text-sm text-slate-400">
        <Spinner /> Loading dashboard...
      </div>
    );
  }

  const maxSeverityCount = Math.max(1, ...Object.values(data.by_severity));

  return (
    <div className="mx-auto max-w-5xl space-y-6 px-6 py-10">
      <h1 className="text-2xl font-semibold text-slate-100">Dashboard</h1>

      <div className="grid gap-4 sm:grid-cols-3">
        <StatTile label="Total Incidents" value={data.total_incidents} />
        <StatTile
          label="Avg Resolution"
          value={data.avg_resolution_minutes != null ? `${Math.round(data.avg_resolution_minutes)}m` : "—"}
        />
        <StatTile label="Currently Active" value={data.recent_investigations.filter((i) => i.status === "running" || i.status === "pending").length} />
      </div>

      <div className="grid gap-4 sm:grid-cols-2">
        <Card>
          <CardHeader title="By Severity" />
          <div className="space-y-2.5">
            {SEVERITY_ORDER.filter((s) => data.by_severity[s]).map((s) => (
              <div key={s} className="flex items-center gap-3">
                <span className="w-16 shrink-0 text-xs capitalize text-slate-400">{s}</span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/5">
                  <div
                    className={`h-full rounded-full ${SEVERITY_COLOR[s]}`}
                    style={{ width: `${(data.by_severity[s] / maxSeverityCount) * 100}%` }}
                  />
                </div>
                <span className="w-6 shrink-0 text-right text-xs tabular-nums text-slate-400">{data.by_severity[s]}</span>
              </div>
            ))}
            {Object.keys(data.by_severity).length === 0 && <p className="text-sm text-slate-500">No data yet.</p>}
          </div>
        </Card>

        <Card>
          <CardHeader title="By Status" />
          <div className="flex flex-wrap gap-2">
            {Object.entries(data.by_status).map(([status, count]) => (
              <div key={status} className="flex items-center gap-2 rounded-lg bg-white/[0.02] px-3 py-2">
                <StatusBadge status={status} />
                <span className="text-sm tabular-nums text-slate-300">{count}</span>
              </div>
            ))}
            {Object.keys(data.by_status).length === 0 && <p className="text-sm text-slate-500">No data yet.</p>}
          </div>
        </Card>
      </div>

      <Card>
        <CardHeader title="Recent Investigations" />
        <div className="space-y-2">
          {data.recent_investigations.map((inv) => (
            <Link
              key={inv.investigation_id}
              to={`/incident/${inv.incident_id}`}
              className="flex items-center justify-between rounded-lg px-3 py-2 text-sm transition-colors hover:bg-white/[0.05]"
            >
              <span className="text-slate-300">Incident #{inv.incident_id}</span>
              <span className="text-slate-500">{inv.current_agent || "—"}</span>
              <StatusBadge status={inv.status} />
            </Link>
          ))}
          {data.recent_investigations.length === 0 && <p className="text-sm text-slate-500">No investigations yet.</p>}
        </div>
      </Card>
    </div>
  );
}
