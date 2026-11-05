from typing import List, Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm

router = APIRouter()


@router.get("/summary", summary="Get Active Brand Knowledge Rules Summary")
def get_brand_knowledge_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the organization's active brand governance rules:
    - Official brand voice & style guidelines
    - Approved factual specifications
    - Restricted terminology dictionary
    """
    guidelines = db.query(BrandGuideline).filter(
        BrandGuideline.organization_id == current_user.organization_id,
        BrandGuideline.is_active == True
    ).all()

    facts = db.query(ApprovedFact).filter(
        ApprovedFact.organization_id == current_user.organization_id,
        ApprovedFact.is_active == True
    ).all()

    terms = db.query(RestrictedTerm).filter(
        RestrictedTerm.organization_id == current_user.organization_id,
        RestrictedTerm.is_active == True
    ).all()

    return {
        "organization_id": current_user.organization_id,
        "guidelines": [
            {
                "id": g.id,
                "category": g.category,
                "title": g.title,
                "description": g.description,
                "rules": g.rules,
                "severity_level": g.severity_level
            }
            for g in guidelines
        ],
        "approved_facts": [
            {
                "id": f.id,
                "topic": f.topic,
                "statement": f.statement,
                "verified_numbers": f.verified_numbers,
                "reference_url_or_doc": f.reference_url_or_doc
            }
            for f in facts
        ],
        "restricted_terms": [
            {
                "id": t.id,
                "term": t.term,
                "category": t.category,
                "severity": t.severity,
                "suggested_alternative": t.suggested_alternative,
                "reason": t.reason
            }
            for t in terms
        ]
    }
