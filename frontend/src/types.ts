export type Severity = "low" | "medium" | "high" | "critical";
export type IncidentStatus = "open" | "investigating" | "resolved";
export type InvestigationStatus = "pending" | "running" | "completed" | "failed";

export interface AgentResult {
  agent_name: string;
  input_summary: string;
  tools_used: string[];
  output: Record<string, unknown>;
  status: string;
  created_at: string;
}

export interface Recommendation {
  action: string;
  category: string;
  rationale: string;
  confidence: number;
}

export interface Postmortem {
  executive_summary: string;
  timeline: string[];
  root_cause: string;
  impact: string;
  fix_applied: string;
  preventive_actions: string[];
  lessons_learned: string[];
}

export interface Investigation {
  id: number;
  status: InvestigationStatus;
  current_agent: string;
  error: string;
  started_at: string | null;
  completed_at: string | null;
  agent_results: AgentResult[];
  recommendations: Recommendation[];
  postmortem: Postmortem | null;
}

export interface Incident {
  id: number;
  title: string;
  description: string;
  severity: Severity;
  status: IncidentStatus;
  created_at: string;
  resolved_at: string | null;
  investigations: Investigation[];
}

export interface IncidentSummary {
  id: number;
  title: string;
  severity: Severity;
  status: IncidentStatus;
  created_at: string;
}

export interface DashboardData {
  total_incidents: number;
  by_severity: Record<string, number>;
  by_status: Record<string, number>;
  avg_resolution_minutes: number | null;
  recent_investigations: {
    investigation_id: number;
    incident_id: number;
    status: string;
    current_agent: string;
  }[];
}

export interface HealthStatus {
  status: string;
  database: boolean;
  chroma: boolean;
  ollama: boolean;
}

export const AGENT_PIPELINE = [
  "log_agent",
  "metrics_agent",
  "k8s_agent",
  "dependency_agent",
  "root_cause_agent",
  "recommendation_agent",
  "postmortem_agent",
] as const;

export const AGENT_LABELS: Record<string, string> = {
  log_agent: "Log Analysis",
  metrics_agent: "Metrics Analysis",
  k8s_agent: "Kubernetes",
  dependency_agent: "Dependency",
  root_cause_agent: "Root Cause",
  recommendation_agent: "Recommendation",
  postmortem_agent: "Postmortem",
};
