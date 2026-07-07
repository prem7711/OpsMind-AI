from fastapi import BackgroundTasks, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.agents.orchestrator import run_investigation
from app.db.models import Feedback, Incident, Investigation, InvestigationStatus, LogArtifact, MetricArtifact, Severity


def create_incident(
    db: Session,
    title: str,
    description: str,
    severity: Severity,
    log_files: list[tuple[str, str]],
    metric_files: list[tuple[str, str]],
) -> Incident:
    incident = Incident(title=title, description=description, severity=severity)
    db.add(incident)
    db.flush()

    for filename, content in log_files:
        db.add(LogArtifact(incident_id=incident.id, filename=filename, content=content))
    for filename, content in metric_files:
        db.add(MetricArtifact(incident_id=incident.id, filename=filename, content=content))

    db.commit()
    db.refresh(incident)
    return incident


def start_analysis(db: Session, background_tasks: BackgroundTasks, incident_id: int) -> Investigation:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")

    investigation = Investigation(incident_id=incident_id, status=InvestigationStatus.pending)
    db.add(investigation)
    db.commit()
    db.refresh(investigation)

    background_tasks.add_task(
        run_investigation, investigation.id, incident_id, incident.title, incident.description
    )
    return investigation


def get_incident(db: Session, incident_id: int) -> Incident:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")
    return incident


def list_history(db: Session, limit: int = 50, offset: int = 0) -> list[Incident]:
    return (
        db.query(Incident)
        .order_by(Incident.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_dashboard(db: Session) -> dict:
    total = db.query(func.count(Incident.id)).scalar() or 0

    by_severity = dict(
        db.query(Incident.severity, func.count(Incident.id)).group_by(Incident.severity).all()
    )
    by_severity = {k.value: v for k, v in by_severity.items()}

    by_status = dict(db.query(Incident.status, func.count(Incident.id)).group_by(Incident.status).all())
    by_status = {k.value: v for k, v in by_status.items()}

    resolved = db.query(Incident).filter(Incident.resolved_at.isnot(None)).all()
    avg_minutes = None
    if resolved:
        deltas = [(i.resolved_at - i.created_at).total_seconds() / 60 for i in resolved]
        avg_minutes = sum(deltas) / len(deltas)

    recent = (
        db.query(Investigation)
        .order_by(Investigation.id.desc())
        .limit(10)
        .all()
    )
    recent_out = [
        {
            "investigation_id": inv.id,
            "incident_id": inv.incident_id,
            "status": inv.status.value,
            "current_agent": inv.current_agent,
        }
        for inv in recent
    ]

    return {
        "total_incidents": total,
        "by_severity": by_severity,
        "by_status": by_status,
        "avg_resolution_minutes": avg_minutes,
        "recent_investigations": recent_out,
    }


def add_feedback(
    db: Session, incident_id: int, investigation_id: int | None, user_id: int | None, rating: int, comment: str
) -> Feedback:
    incident = db.get(Incident, incident_id)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident not found")

    feedback = Feedback(
        incident_id=incident_id,
        investigation_id=investigation_id,
        user_id=user_id,
        rating=rating,
        comment=comment,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback
