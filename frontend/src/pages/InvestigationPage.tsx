import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getIncident, submitFeedback } from "../api/client";
import { AGENT_LABELS, AGENT_PIPELINE, type Incident } from "../types";
import { AgentResultCard } from "../components/AgentResultCard";
import { AgentTimeline } from "../components/AgentTimeline";
import { Card, CardHeader } from "../components/Card";
import { PostmortemView } from "../components/PostmortemView";
import { RecommendationList } from "../components/RecommendationList";
import { SeverityBadge, StatusBadge } from "../components/Badge";
import { Spinner } from "../components/Spinner";
import { FeedbackForm } from "../components/FeedbackForm";

const POLL_MS = 3000;

export function InvestigationPage() {
  const { incidentId } = useParams();
  const [incident, setIncident] = useState<Incident | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!incidentId) return;
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;

    async function poll() {
      try {
        const data = await getIncident(Number(incidentId));
        if (cancelled) return;
        setIncident(data);
        const investigation = data.investigations.at(-1);
        const active = investigation && (investigation.status === "pending" || investigation.status === "running");
        if (active) timer = setTimeout(poll, POLL_MS);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "failed to load incident");
      }
    }
    poll();
    return () => {
      cancelled = true;
      clearTimeout(timer);
    };
  }, [incidentId]);

  if (error) {
    return <div className="mx-auto max-w-4xl px-6 py-10 text-sm text-rose-400">{error}</div>;
  }
  if (!incident) {
    return (
      <div className="mx-auto flex max-w-4xl items-center gap-2 px-6 py-10 text-sm text-slate-400">
        <Spinner /> Loading incident...
      </div>
    );
  }

  const investigation = incident.investigations.at(-1);
  // recommendation_agent and postmortem_agent's outputs are rendered in full by the dedicated
  // <RecommendationList> / <PostmortemView> cards below, so skip their raw cards here.
  const RENDERED_ELSEWHERE = new Set(["recommendation_agent", "postmortem_agent"]);
  const orderedResults = investigation
    ? AGENT_PIPELINE.filter((name) => !RENDERED_ELSEWHERE.has(name))
        .map((name) => investigation.agent_results.find((r) => r.agent_name === name))
        .filter(Boolean)
    : [];

  return (
    <div className="mx-auto max-w-4xl space-y-6 px-6 py-10">
      <div>
        <div className="mb-2 flex items-center gap-2">
          <SeverityBadge severity={incident.severity} />
          <StatusBadge status={incident.status} />
        </div>
        <h1 className="text-2xl font-semibold text-slate-100">{incident.title}</h1>
        {incident.description && <p className="mt-1.5 text-sm text-slate-400">{incident.description}</p>}
      </div>

      {investigation ? (
        <>
          <Card>
            <CardHeader
              title="Investigation Pipeline"
              subtitle={
                investigation.status === "failed"
                  ? `Failed: ${investigation.error}`
                  : investigation.status === "completed"
                    ? "All agents completed"
                    : `Running — ${AGENT_LABELS[investigation.current_agent] ?? "starting"}`
              }
              right={<StatusBadge status={investigation.status} />}
            />
            <AgentTimeline investigation={investigation} />
          </Card>

          {orderedResults.map((result) => result && <AgentResultCard key={result.agent_name} result={result} />)}

          <RecommendationList recommendations={investigation.recommendations} />

          {investigation.postmortem && <PostmortemView postmortem={investigation.postmortem} />}

          {investigation.status === "completed" && (
            <FeedbackForm incidentId={incident.id} investigationId={investigation.id} onSubmit={submitFeedback} />
          )}
        </>
      ) : (
        <Card>
          <p className="text-sm text-slate-400">No investigation has been started for this incident yet.</p>
        </Card>
      )}
    </div>
  );
}
