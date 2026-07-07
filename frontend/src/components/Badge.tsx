const SEVERITY_STYLES: Record<string, string> = {
  low: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/30",
  medium: "bg-amber-500/10 text-amber-400 ring-amber-500/30",
  high: "bg-orange-500/10 text-orange-400 ring-orange-500/30",
  critical: "bg-rose-500/10 text-rose-400 ring-rose-500/30",
};

const STATUS_STYLES: Record<string, string> = {
  open: "bg-sky-500/10 text-sky-400 ring-sky-500/30",
  investigating: "bg-violet-500/10 text-violet-400 ring-violet-500/30",
  resolved: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/30",
  pending: "bg-slate-500/10 text-slate-400 ring-slate-500/30",
  running: "bg-violet-500/10 text-violet-400 ring-violet-500/30",
  completed: "bg-emerald-500/10 text-emerald-400 ring-emerald-500/30",
  failed: "bg-rose-500/10 text-rose-400 ring-rose-500/30",
};

function Badge({ label, styles }: { label: string; styles: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-xs font-medium ring-1 ring-inset ${styles}`}
    >
      <span className="h-1.5 w-1.5 rounded-full bg-current" />
      {label}
    </span>
  );
}

export function SeverityBadge({ severity }: { severity: string }) {
  return <Badge label={severity} styles={SEVERITY_STYLES[severity] ?? SEVERITY_STYLES.medium} />;
}

export function StatusBadge({ status }: { status: string }) {
  return <Badge label={status.replace("_", " ")} styles={STATUS_STYLES[status] ?? STATUS_STYLES.pending} />;
}
