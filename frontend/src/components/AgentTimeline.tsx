import { AGENT_LABELS, AGENT_PIPELINE, type Investigation } from "../types";
import { Spinner } from "./Spinner";

export function AgentTimeline({ investigation }: { investigation: Investigation }) {
  const doneAgents = new Set(investigation.agent_results.map((r) => r.agent_name));
  const isTerminal = investigation.status === "completed" || investigation.status === "failed";

  return (
    <div className="flex flex-wrap items-center gap-2">
      {AGENT_PIPELINE.map((agent, i) => {
        const done = doneAgents.has(agent);
        const active = !done && !isTerminal && investigation.current_agent === agent;
        return (
          <div key={agent} className="flex items-center gap-2">
            <div
              className={`flex items-center gap-2 rounded-full px-3 py-1.5 text-xs font-medium ring-1 ring-inset transition-colors ${
                done
                  ? "bg-emerald-500/10 text-emerald-400 ring-emerald-500/30"
                  : active
                    ? "bg-violet-500/10 text-violet-300 ring-violet-500/40"
                    : "bg-white/[0.03] text-slate-500 ring-white/10"
              }`}
            >
              {active ? <Spinner className="h-3 w-3" /> : done ? <CheckIcon /> : <span className="h-1.5 w-1.5 rounded-full bg-current" />}
              {AGENT_LABELS[agent]}
            </div>
            {i < AGENT_PIPELINE.length - 1 && <div className="h-px w-4 bg-white/10" />}
          </div>
        );
      })}
    </div>
  );
}

function CheckIcon() {
  return (
    <svg viewBox="0 0 20 20" fill="currentColor" className="h-3 w-3">
      <path
        fillRule="evenodd"
        d="M16.704 5.29a1 1 0 010 1.415l-7.5 7.5a1 1 0 01-1.415 0l-3.5-3.5a1 1 0 111.415-1.414l2.792 2.792 6.793-6.793a1 1 0 011.415 0z"
        clipRule="evenodd"
      />
    </svg>
  );
}
