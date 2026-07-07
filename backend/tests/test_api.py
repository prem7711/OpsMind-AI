import io

from fastapi.testclient import TestClient

import app.services.incident_service as incident_service
from app.db.base import SessionLocal
from app.db.models import Investigation, InvestigationStatus
from app.main import app


def _stub_run_investigation(investigation_id, incident_id, title, description):
    db = SessionLocal()
    try:
        inv = db.get(Investigation, investigation_id)
        inv.status = InvestigationStatus.completed
        db.commit()
    finally:
        db.close()


def test_full_incident_flow(monkeypatch, db_session):
    monkeypatch.setattr(incident_service, "run_investigation", _stub_run_investigation)
    client = TestClient(app)

    resp = client.post(
        "/incident/upload",
        data={"title": "API 500s", "description": "spike in errors", "severity": "high"},
        files={"log_files": ("app.log", io.BytesIO(b"ERROR db timeout"), "text/plain")},
    )
    assert resp.status_code == 200, resp.text
    incident_id = resp.json()["incident_id"]

    resp = client.post("/incident/analyze", json={"incident_id": incident_id})
    assert resp.status_code == 200, resp.text
    investigation_id = resp.json()["investigation_id"]
    assert resp.json()["status"] in ("pending", "completed")

    resp = client.get(f"/incident/{incident_id}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["title"] == "API 500s"
    assert body["investigations"][0]["status"] == "completed"

    resp = client.get("/incident/history")
    assert resp.status_code == 200
    assert len(resp.json()) == 1

    resp = client.get("/dashboard")
    assert resp.status_code == 200
    assert resp.json()["total_incidents"] == 1

    resp = client.post(
        "/feedback",
        json={"incident_id": incident_id, "investigation_id": investigation_id, "rating": 5, "comment": "great"},
    )
    assert resp.status_code == 200, resp.text

    resp = client.get("/health")
    assert resp.status_code == 200
    assert "status" in resp.json()


def test_incident_not_found():
    client = TestClient(app)
    resp = client.get("/incident/999999")
    assert resp.status_code == 404
