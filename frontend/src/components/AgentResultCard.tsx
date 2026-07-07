import { AGENT_LABELS, type AgentResult } from "../types";
import { Card, CardHeader } from "./Card";

function humanizeKey(key: string): string {
  return key.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function ObjectItem({ item }: { item: Record<string, unknown> }) {
  return (
    <div className="rounded-lg border border-white/5 bg-white/[0.02] px-3 py-2">
      {Object.entries(item).map(([k, v]) => (
        <div key={k} className="flex gap-2 text-sm">
          <span className="shrink-0 text-slate-500">{humanizeKey(k)}:</span>
          <span className="text-slate-300">{String(v)}</span>
        </div>
      ))}
    </div>
  );
}

function OutputValue({ value }: { value: unknown }) {
  if (Array.isArray(value)) {
    if (value.length === 0) return <span className="text-slate-500">none</span>;
    if (typeof value[0] === "object" && value[0] !== null) {
      return (
        <div className="space-y-1.5">
          {value.map((item, i) => (
            <ObjectItem key={i} item={item as Record<string, unknown>} />
          ))}
        </div>
      );
    }
    return (
      <ul className="ml-4 list-disc space-y-1 text-slate-300">
        {value.map((item, i) => (
          <li key={i}>{String(item)}</li>
        ))}
      </ul>
    );
  }
  if (typeof value === "number") {
    return <span className="text-slate-300">{value}</span>;
  }
  return <p className="text-slate-300">{String(value)}</p>;
}

// Rendered by a dedicated component elsewhere; skip here to avoid showing it twice.
const DUPLICATE_KEYS = new Set(["recommendations"]);

export function AgentResultCard({ result }: { result: AgentResult }) {
  const entries = Object.entries(result.output).filter(([key]) => !DUPLICATE_KEYS.has(key));
  return (
    <Card>
      <CardHeader
        title={AGENT_LABELS[result.agent_name] ?? result.agent_name}
        subtitle={new Date(result.created_at).toLocaleString()}
        right={
          result.tools_used.length > 0 && (
            <div className="flex flex-wrap justify-end gap-1">
              {result.tools_used.map((t) => (
                <span
                  key={t}
                  className="rounded-md bg-indigo-500/10 px-1.5 py-0.5 font-mono text-[10px] text-indigo-300 ring-1 ring-inset ring-indigo-500/20"
                >
                  {t}
                </span>
              ))}
            </div>
          )
        }
      />
      <div className="space-y-3 text-sm">
        {entries.map(([key, value]) => (
          <div key={key}>
            <div className="mb-1 text-xs font-medium uppercase tracking-wide text-slate-500">{humanizeKey(key)}</div>
            <OutputValue value={value} />
          </div>
        ))}
      </div>
    </Card>
  );
}
