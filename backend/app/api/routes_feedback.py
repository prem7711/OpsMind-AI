from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.schemas import FeedbackIn
from app.services import incident_service

router = APIRouter(tags=["feedback"])


@router.post("/feedback")
def submit_feedback(payload: FeedbackIn, db: Session = Depends(get_db)):
    feedback = incident_service.add_feedback(
        db, payload.incident_id, payload.investigation_id, payload.user_id, payload.rating, payload.comment
    )
    return {"feedback_id": feedback.id}
