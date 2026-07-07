from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.db.models import IncidentStatus, InvestigationStatus, Severity


class IncidentCreateResponse(BaseModel):
    incident_id: int


class AnalyzeRequest(BaseModel):
    incident_id: int


class AnalyzeResponse(BaseModel):
    investigation_id: int
    status: InvestigationStatus


class AgentResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    agent_name: str
    input_summary: str
    tools_used: list
    output: dict
    status: str
    created_at: datetime


class RecommendationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    action: str
    category: str
    rationale: str
    confidence: float


class PostmortemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    executive_summary: str
    timeline: list
    root_cause: str
    impact: str
    fix_applied: str
    preventive_actions: list
    lessons_learned: list


class InvestigationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: InvestigationStatus
    current_agent: str
    error: str
    started_at: datetime | None
    completed_at: datetime | None
    agent_results: list[AgentResultOut] = []
    recommendations: list[RecommendationOut] = []
    postmortem: PostmortemOut | None = None


class IncidentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    severity: Severity
    status: IncidentStatus
    created_at: datetime
    resolved_at: datetime | None
    investigations: list[InvestigationOut] = []


class IncidentSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    severity: Severity
    status: IncidentStatus
    created_at: datetime


class DashboardOut(BaseModel):
    total_incidents: int
    by_severity: dict[str, int]
    by_status: dict[str, int]
    avg_resolution_minutes: float | None
    recent_investigations: list[dict]


class FeedbackIn(BaseModel):
    incident_id: int
    investigation_id: int | None = None
    user_id: int | None = None
    rating: int
    comment: str = ""


class HealthOut(BaseModel):
    status: str
    database: bool
    chroma: bool
    ollama: bool
