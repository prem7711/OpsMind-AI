from app.agents import (
    dependency_agent,
    k8s_agent,
    log_agent,
    metrics_agent,
    postmortem_agent,
    recommendation_agent,
    root_cause_agent,
)
from app.agents.orchestrator import run_investigation
from app.db.models import AgentResult, Incident, Investigation, InvestigationStatus, Recommendation, Postmortem


class _FakeAgent:
    def __init__(self, output: dict, tools_used: list):
        self._output = output
        self._tools_used = tools_used

    def run(self, task: str) -> dict:
        return {"output": self._output, "tools_used": self._tools_used, "message_count": 3}


def _patch_all_agents(monkeypatch):
    monkeypatch.setattr(log_agent, "build", lambda ctx: _FakeAgent(
        {"summary": "errors found", "error_patterns": ["timeout"], "suspected_components": ["api"], "severity_assessment": "high"},
        ["search_logs"],
    ))
    monkeypatch.setattr(metrics_agent, "build", lambda ctx: _FakeAgent(
        {"summary": "cpu spike", "anomalies": ["cpu 97%"], "suspected_components": ["api"], "severity_assessment": "high"},
        ["detect_anomaly"],
    ))
    monkeypatch.setattr(k8s_agent, "build", lambda ctx: _FakeAgent(
        {"summary": "pod crashlooping", "unhealthy_resources": ["api-server pod"], "suspected_components": ["api"], "severity_assessment": "high"},
        ["get_pod_status"],
    ))
    monkeypatch.setattr(dependency_agent, "build", lambda ctx: _FakeAgent(
        {"summary": "postgres degraded", "unhealthy_services": ["postgres"], "dependency_chain": ["api", "postgres"], "severity_assessment": "high"},
        ["check_service_health"],
    ))
    monkeypatch.setattr(root_cause_agent, "build", lambda ctx: _FakeAgent(
        {"root_cause": "DB connection pool exhaustion", "contributing_factors": ["traffic spike"], "affected_components": ["api", "postgres"], "confidence": 0.9},
        [],
    ))
    monkeypatch.setattr(recommendation_agent, "build", lambda ctx: _FakeAgent(
        {"recommendations": [{"action": "increase DB pool size", "category": "scale", "rationale": "pool exhausted", "confidence": 0.9}]},
        [],
    ))
    monkeypatch.setattr(postmortem_agent, "build", lambda ctx: _FakeAgent(
        {
            "executive_summary": "DB pool exhaustion caused API errors.",
            "timeline": ["10:00 spike started", "10:05 pool exhausted"],
            "root_cause": "DB connection pool exhaustion",
            "impact": "API errors for 15 minutes",
            "fix_applied": "increased pool size",
            "preventive_actions": ["add pool utilization alert"],
            "lessons_learned": ["alert earlier on pool saturation"],
        },
        [],
    ))


def test_run_investigation_completes_and_persists(db_session, monkeypatch):
    _patch_all_agents(monkeypatch)

    incident = Incident(title="API errors", description="Spike in 500s")
    db_session.add(incident)
    db_session.commit()

    investigation = Investigation(incident_id=incident.id, status=InvestigationStatus.pending)
    db_session.add(investigation)
    db_session.commit()

    run_investigation(investigation.id, incident.id, incident.title, incident.description)

    db_session.refresh(investigation)
    assert investigation.status == InvestigationStatus.completed
    assert investigation.completed_at is not None

    results = db_session.query(AgentResult).filter_by(investigation_id=investigation.id).all()
    assert {r.agent_name for r in results} == {
        "log_agent", "metrics_agent", "k8s_agent", "dependency_agent",
        "root_cause_agent", "recommendation_agent", "postmortem_agent",
    }

    recs = db_session.query(Recommendation).filter_by(investigation_id=investigation.id).all()
    assert len(recs) == 1
    assert recs[0].category == "scale"

    postmortem = db_session.query(Postmortem).filter_by(investigation_id=investigation.id).first()
    assert postmortem is not None
    assert postmortem.root_cause == "DB connection pool exhaustion"
