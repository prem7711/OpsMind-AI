import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { analyzeIncident, uploadIncident } from "../api/client";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import type { Severity } from "../types";

const SEVERITIES: Severity[] = ["low", "medium", "high", "critical"];

export function UploadPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [severity, setSeverity] = useState<Severity>("high");
  const [logFiles, setLogFiles] = useState<File[]>([]);
  const [metricFiles, setMetricFiles] = useState<File[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const { incident_id } = await uploadIncident({ title, description, severity, logFiles, metricFiles });
      await analyzeIncident(incident_id);
      navigate(`/incident/${incident_id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "upload failed");
      setSubmitting(false);
    }
  }

  return (
    <div className="mx-auto max-w-2xl px-6 py-10">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-slate-100">Report an Incident</h1>
        <p className="mt-1.5 text-sm text-slate-400">
          Upload logs and metrics — Sentinel's seven agents will investigate and produce a postmortem.
        </p>
      </div>

      <Card>
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">Title</label>
            <input
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="API 500 spike on checkout service"
              className="w-full rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none ring-indigo-500/50 focus:ring-2"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">Description</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={3}
              placeholder="What happened, when, and what you've observed so far..."
              className="w-full resize-none rounded-lg border border-white/10 bg-white/[0.03] px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 outline-none ring-indigo-500/50 focus:ring-2"
            />
          </div>

          <div>
            <label className="mb-1.5 block text-sm font-medium text-slate-300">Severity</label>
            <div className="flex gap-2">
              {SEVERITIES.map((s) => (
                <button
                  type="button"
                  key={s}
                  onClick={() => setSeverity(s)}
                  className={`rounded-lg px-3.5 py-1.5 text-sm font-medium capitalize ring-1 ring-inset transition-colors ${
                    severity === s
                      ? "bg-indigo-500/20 text-indigo-300 ring-indigo-500/40"
                      : "bg-white/[0.02] text-slate-400 ring-white/10 hover:bg-white/5"
                  }`}
                >
                  {s}
                </button>
              ))}
            </div>
          </div>

          <div className="grid gap-5 sm:grid-cols-2">
            <FileField label="Log files" files={logFiles} onChange={setLogFiles} />
            <FileField label="Metric files" files={metricFiles} onChange={setMetricFiles} />
          </div>

          {error && (
            <div className="rounded-lg bg-rose-500/10 px-3.5 py-2.5 text-sm text-rose-300 ring-1 ring-inset ring-rose-500/30">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting || !title}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-gradient-to-r from-indigo-500 to-violet-600 px-4 py-2.5 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 transition-opacity disabled:opacity-50"
          >
            {submitting && <Spinner />}
            {submitting ? "Starting investigation..." : "Upload & Analyze"}
          </button>
        </form>
      </Card>
    </div>
  );
}

function FileField({
  label,
  files,
  onChange,
}: {
  label: string;
  files: File[];
  onChange: (files: File[]) => void;
}) {
  return (
    <div>
      <label className="mb-1.5 block text-sm font-medium text-slate-300">{label}</label>
      <label className="flex cursor-pointer flex-col items-center justify-center rounded-lg border border-dashed border-white/15 bg-white/[0.02] px-4 py-6 text-center transition-colors hover:bg-white/[0.04]">
        <span className="text-xs text-slate-400">
          {files.length > 0 ? files.map((f) => f.name).join(", ") : "Click to select file(s)"}
        </span>
        <input
          type="file"
          multiple
          className="hidden"
          onChange={(e) => onChange(Array.from(e.target.files ?? []))}
        />
      </label>
    </div>
  );
}
