from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, submissions, analysis, reviews, publishing, brand_knowledge, admin

api_router = APIRouter()
api_router.include_router(health.router, tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication & RBAC"])
api_router.include_router(admin.router, prefix="/admin", tags=["Admin Operations"])
api_router.include_router(submissions.router, prefix="/submissions", tags=["Content Submissions"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["Content Compliance Analysis"])
api_router.include_router(brand_knowledge.router, prefix="/brand-knowledge", tags=["Brand Knowledge Hub"])
api_router.include_router(reviews.router, prefix="/reviews", tags=["Human Review Workflow"])
api_router.include_router(publishing.router, prefix="/publishing", tags=["Internal Publishing & Public Preview"])
