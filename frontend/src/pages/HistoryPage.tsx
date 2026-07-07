import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { getHistory } from "../api/client";
import { Card } from "../components/Card";
import { SeverityBadge, StatusBadge } from "../components/Badge";
import { Spinner } from "../components/Spinner";
import type { IncidentSummary } from "../types";

export function HistoryPage() {
  const [incidents, setIncidents] = useState<IncidentSummary[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHistory()
      .then(setIncidents)
      .catch((err) => setError(err instanceof Error ? err.message : "failed to load history"));
  }, []);

  return (
    <div className="mx-auto max-w-4xl px-6 py-10">
      <h1 className="mb-6 text-2xl font-semibold text-slate-100">Incident History</h1>

      {error && <p className="text-sm text-rose-400">{error}</p>}

      {!incidents && !error && (
        <div className="flex items-center gap-2 text-sm text-slate-400">
          <Spinner /> Loading...
        </div>
      )}

      {incidents && incidents.length === 0 && (
        <Card>
          <p className="text-sm text-slate-400">No incidents reported yet.</p>
        </Card>
      )}

      <div className="space-y-2.5">
        {incidents?.map((incident) => (
          <Link key={incident.id} to={`/incident/${incident.id}`}>
            <Card className="transition-colors hover:bg-white/[0.05]">
              <div className="flex items-center justify-between gap-4">
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-slate-100">{incident.title}</p>
                  <p className="mt-0.5 text-xs text-slate-500">{new Date(incident.created_at).toLocaleString()}</p>
                </div>
                <div className="flex shrink-0 items-center gap-2">
                  <SeverityBadge severity={incident.severity} />
                  <StatusBadge status={incident.status} />
                </div>
              </div>
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
}
