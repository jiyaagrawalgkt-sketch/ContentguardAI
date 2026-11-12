from typing import List, Optional
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.permissions import require_compliance, require_compliance_or_reviewer
from app.models.user import User
from app.models.audit import AuditLog
from app.models.knowledge_base import ExtractedClaim, ClaimVerificationStatus
from app.models.submission import ContentSubmission

router = APIRouter()


@router.get("/audit-logs", summary="Query Append-Only Audit Trail")
def get_audit_trail(
    action: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(require_compliance),
    db: Session = Depends(get_db),
):
    """
    Immutable, append-only governance trail query.
    Restricted strictly to Compliance Officers and Organization Admins.
    """
    query = db.query(AuditLog).filter(
        AuditLog.organization_id == current_user.organization_id
    )

    if action:
        query = query.filter(AuditLog.action == action)
    if entity_type:
        query = query.filter(AuditLog.entity_type == entity_type)

    total = query.count()
    logs = query.order_by(desc(AuditLog.created_at)).offset(offset).limit(limit).all()

    items = []
    for log in logs:
        items.append({
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "actor_id": log.user_id,
            "actor_email": log.user.email if log.user else "System",
            "actor_name": log.user.full_name if log.user else "System Process",
            "actor_role": log.user.role if log.user else "system",
            "details": log.details,
            "timestamp": log.created_at.isoformat(),
        })

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "logs": items,
    }


@router.get("/claims-queue", summary="Compliance Officer Verification Queue")
def get_compliance_claims_queue(
    status_filter: Optional[str] = Query(None),
    current_user: User = Depends(require_compliance_or_reviewer),
    db: Session = Depends(get_db),
):
    """
    List high-severity or flagged claims (unsupported, conflicting, outdated)
    awaiting regulatory, legal, or compliance review.
    """
    query = db.query(ExtractedClaim).filter(
        ExtractedClaim.organization_id == current_user.organization_id
    )

    if status_filter:
        query = query.filter(ExtractedClaim.verification_status == status_filter)
    else:
        # Default to claims that require attention
        query = query.filter(
            ExtractedClaim.verification_status.in_([
                ClaimVerificationStatus.UNSUPPORTED.value,
                ClaimVerificationStatus.CONFLICTING.value,
                ClaimVerificationStatus.OUTDATED.value,
            ])
        )

    claims = query.order_by(desc(ExtractedClaim.created_at)).limit(50).all()

    items = []
    for c in claims:
        items.append({
            "id": c.id,
            "submission_id": c.submission_id,
            "submission_title": c.submission.title if c.submission else "Unknown",
            "claim_text": c.claim_text,
            "claim_type": c.claim_type,
            "verification_status": c.verification_status,
            "severity": c.severity,
            "explanation": c.explanation,
            "source_document_name": c.source_document_name,
            "source_passage": c.source_passage,
            "suggested_correction": c.suggested_correction,
            "created_at": c.created_at.isoformat(),
        })

    return items


@router.post("/certify-claim/{claim_id}", summary="Compliance Officer Claim Certification")
def certify_claim(
    claim_id: str,
    payload: dict = Body(...),
    current_user: User = Depends(require_compliance),
    db: Session = Depends(get_db),
):
    """
    Compliance officer manual validation or risk acceptance of a flagged claim.
    Requires justification note.
    """
    claim = db.query(ExtractedClaim).filter(
        ExtractedClaim.id == claim_id,
        ExtractedClaim.organization_id == current_user.organization_id
    ).first()

    if not claim:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Claim record not found")

    decision = payload.get("decision", "supported")  # supported or rejected
    note = payload.get("note", "Certified by Compliance Officer")

    claim.verification_status = decision
    claim.explanation = f"{claim.explanation} | Compliance Decision: {note} (by {current_user.full_name})"
    claim.recommended_action = "Approve" if decision == "supported" else "Remove"

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CLAIM_COMPLIANCE_CERTIFIED",
        entity_type="extracted_claim",
        entity_id=claim.id,
        details={"claim_text": claim.claim_text, "decision": decision, "note": note}
    )
    db.add(audit)
    db.commit()

    return {
        "id": claim.id,
        "verification_status": claim.verification_status,
        "message": f"Claim status updated to '{decision}' by Compliance Officer."
    }
