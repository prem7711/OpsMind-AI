import type { DashboardData, HealthStatus, Incident, IncidentSummary } from "../types";

const BASE = "/api";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: init?.body instanceof FormData ? init.headers : { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${body}`);
  }
  return res.json() as Promise<T>;
}

export async function uploadIncident(params: {
  title: string;
  description: string;
  severity: string;
  logFiles: File[];
  metricFiles: File[];
}): Promise<{ incident_id: number }> {
  const form = new FormData();
  form.append("title", params.title);
  form.append("description", params.description);
  form.append("severity", params.severity);
  params.logFiles.forEach((f) => form.append("log_files", f));
  params.metricFiles.forEach((f) => form.append("metric_files", f));
  return request("/incident/upload", { method: "POST", body: form });
}

export async function analyzeIncident(incidentId: number): Promise<{ investigation_id: number; status: string }> {
  return request("/incident/analyze", {
    method: "POST",
    body: JSON.stringify({ incident_id: incidentId }),
  });
}

export async function getIncident(incidentId: number): Promise<Incident> {
  return request(`/incident/${incidentId}`);
}

export async function getHistory(): Promise<IncidentSummary[]> {
  return request("/incident/history");
}

export async function getDashboard(): Promise<DashboardData> {
  return request("/dashboard");
}

export async function getHealth(): Promise<HealthStatus> {
  return request("/health");
}

export async function submitFeedback(params: {
  incidentId: number;
  investigationId?: number;
  rating: number;
  comment: string;
}): Promise<{ feedback_id: number }> {
  return request("/feedback", {
    method: "POST",
    body: JSON.stringify({
      incident_id: params.incidentId,
      investigation_id: params.investigationId ?? null,
      rating: params.rating,
      comment: params.comment,
    }),
  });
}
