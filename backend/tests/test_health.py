from app.main import root_redirect
from app.api.v1.endpoints.health import health_check
from app.core.database import SessionLocal


def test_root_endpoint():
    data = root_redirect()
    assert "ContentGuard AI" in data["message"]
    assert "docs" in data
    assert "health" in data


def test_health_endpoint():
    db = SessionLocal()
    try:
        data = health_check(db=db)
        assert data["status"] in ["healthy", "degraded"]
        assert data["service"] == "ContentGuard AI"
        assert "ai_engine" in data
        assert "uptime_seconds" in data
        assert data["database"] == "connected"
    finally:
        db.close()
