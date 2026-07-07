import httpx
from fastapi import APIRouter
from sqlalchemy import text

from app.config import settings
from app.db.base import engine
from app.schemas import HealthOut

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthOut)
def health():
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        pass

    chroma_ok = False
    try:
        from app.rag.retriever import get_vectorstore

        get_vectorstore()._collection.count()
        chroma_ok = True
    except Exception:
        pass

    ollama_ok = False
    try:
        resp = httpx.get(f"{settings.ollama_base_url}/api/tags", timeout=3)
        ollama_ok = resp.status_code == 200
    except Exception:
        pass

    overall = "ok" if (db_ok and chroma_ok and ollama_ok) else "degraded"
    return HealthOut(status=overall, database=db_ok, chroma=chroma_ok, ollama=ollama_ok)
