import time
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db

router = APIRouter()
start_time = time.time()


@router.get("/health", summary="System Health & Diagnostics")
def health_check(db: Session = Depends(get_db)):
    """
    Returns system status, database connectivity, and engine availability.
    """
    db_status = "connected"
    try:
        db.execute(text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    gemini_status = "configured" if settings.GEMINI_API_KEY else "deterministic_fallback_mode"

    return {
        "status": "healthy" if "unhealthy" not in db_status else "degraded",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "uptime_seconds": round(time.time() - start_time, 2),
        "database": db_status,
        "ai_engine": {
            "mode": "hybrid_gemini" if settings.GEMINI_API_KEY else "deterministic_rule_engine",
            "gemini_status": gemini_status,
            "active_model": settings.GEMINI_MODEL if settings.GEMINI_API_KEY else "local_rule_engine"
        }
    }
