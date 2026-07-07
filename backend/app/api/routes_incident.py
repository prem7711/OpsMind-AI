from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.db.models import Severity
from app.schemas import AnalyzeRequest, AnalyzeResponse, IncidentCreateResponse, IncidentOut, IncidentSummary
from app.services import incident_service

router = APIRouter(prefix="/incident", tags=["incident"])


@router.post("/upload", response_model=IncidentCreateResponse)
async def upload_incident(
    title: str = Form(...),
    description: str = Form(""),
    severity: Severity = Form(Severity.medium),
    log_files: list[UploadFile] = File(default_factory=list),
    metric_files: list[UploadFile] = File(default_factory=list),
    db: Session = Depends(get_db),
):
    logs = [(f.filename or "log.txt", (await f.read()).decode(errors="replace")) for f in log_files]
    metrics = [(f.filename or "metrics.txt", (await f.read()).decode(errors="replace")) for f in metric_files]
    incident = incident_service.create_incident(db, title, description, severity, logs, metrics)
    return IncidentCreateResponse(incident_id=incident.id)


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze_incident(payload: AnalyzeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    investigation = incident_service.start_analysis(db, background_tasks, payload.incident_id)
    return AnalyzeResponse(investigation_id=investigation.id, status=investigation.status)


@router.get("/history", response_model=list[IncidentSummary])
def incident_history(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)):
    return incident_service.list_history(db, limit, offset)


@router.get("/{incident_id}", response_model=IncidentOut)
def get_incident(incident_id: int, db: Session = Depends(get_db)):
    return incident_service.get_incident(db, incident_id)
