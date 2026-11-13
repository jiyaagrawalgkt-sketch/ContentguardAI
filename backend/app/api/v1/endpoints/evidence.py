import uuid
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_any_authenticated
from app.models.user import User
from app.models.submission import ContentSubmission
from app.models.knowledge_base import ExtractedClaim
from app.models.audit import AuditLog
from app.engine.evidence_engine import (
    extract_factual_claims,
    verify_claims_against_evidence,
    build_evidence_graph_data,
)

router = APIRouter()


@router.post("/verify/{submission_id}", summary="Verify Claims for Submission")
@router.post("/reverify/{submission_id}", summary="Re-Verify Claims for Submission")
def verify_submission_evidence(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """
    Extract factual, numerical, supremacy, and certification claims from the submission's
    current version, and verify against organization's approved knowledge base documents.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Get latest version content
    content_body = ""
    if submission.current_version_id:
        current_ver = next((v for v in submission.versions if v.id == submission.current_version_id), None)
        if current_ver:
            content_body = current_ver.content_body
    if not content_body and submission.versions:
        content_body = submission.versions[-1].content_body

    if not content_body:
        return {"submission_id": submission_id, "total_claims": 0, "claims": []}

    # 1. Extract raw factual claims
    raw_claims = extract_factual_claims(content_body)

    # 2. Verify against knowledge base
    verified_results = verify_claims_against_evidence(
        claims=raw_claims,
        organization_id=current_user.organization_id,
        db=db,
    )

    # 3. Clean previous claims for this submission and persist newly verified ones
    db.query(ExtractedClaim).filter(ExtractedClaim.submission_id == submission_id).delete()

    persisted_claims = []
    for item in verified_results:
        claim_obj = ExtractedClaim(
            id=str(uuid.uuid4()),
            submission_id=submission_id,
            organization_id=current_user.organization_id,
            claim_text=item["claim_text"],
            claim_type=item["claim_type"],
            verification_status=item["verification_status"],
            severity=item["severity"],
            confidence=item["confidence"],
            explanation=item["explanation"],
            retrieved_evidence_text=item["retrieved_evidence_text"],
            source_document_id=item["source_document_id"],
            source_document_name=item["source_document_name"],
            source_passage=item["source_passage"],
            source_validity_date=item["source_validity_date"],
            recommended_action=item["recommended_action"],
            suggested_correction=item["suggested_correction"],
        )
        db.add(claim_obj)
        persisted_claims.append(claim_obj)

    # 4. Audit Log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="EVIDENCE_VERIFICATION_COMPLETED",
        entity_type="submission",
        entity_id=submission_id,
        details={
            "total_claims": len(persisted_claims),
            "supported": sum(1 for c in persisted_claims if c.verification_status == "supported"),
            "unsupported": sum(1 for c in persisted_claims if c.verification_status == "unsupported"),
            "conflicting": sum(1 for c in persisted_claims if c.verification_status == "conflicting"),
            "outdated": sum(1 for c in persisted_claims if c.verification_status == "outdated"),
        }
    )
    db.add(audit)
    db.commit()

    return {
        "submission_id": submission_id,
        "total_claims": len(persisted_claims),
        "claims": [
            {
                "id": c.id,
                "claim_text": c.claim_text,
                "claim_type": c.claim_type,
                "verification_status": c.verification_status,
                "severity": c.severity,
                "confidence": c.confidence,
                "explanation": c.explanation,
                "source_document_name": c.source_document_name,
                "source_passage": c.source_passage,
                "source_validity_date": c.source_validity_date.isoformat() if c.source_validity_date else None,
                "suggested_correction": c.suggested_correction,
                "recommended_action": c.recommended_action,
            }
            for c in persisted_claims
        ]
    }


@router.get("/claims/{submission_id}", summary="Get Extracted Claims for Submission")
def get_submission_claims(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """Retrieve all claims and supporting evidence records for a given submission.
    Auto-extracts and verifies on-the-fly if no claims are persisted yet."""
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    claims = db.query(ExtractedClaim).filter(
        ExtractedClaim.submission_id == submission_id,
        ExtractedClaim.organization_id == current_user.organization_id
    ).all()

    # If no claims yet, run auto extraction & verification so Creator & Reviewer see live data
    if not claims:
        content_body = ""
        if submission.current_version_id:
            current_ver = next((v for v in submission.versions if v.id == submission.current_version_id), None)
            if current_ver:
                content_body = current_ver.content_body
        if not content_body and submission.versions:
            content_body = submission.versions[-1].content_body

        if content_body and content_body.strip():
            raw_claims = extract_factual_claims(content_body)
            verified = verify_claims_against_evidence(raw_claims, current_user.organization_id, db)
            for item in verified:
                c = ExtractedClaim(
                    id=str(uuid.uuid4()),
                    submission_id=submission_id,
                    organization_id=current_user.organization_id,
                    claim_text=item["claim_text"],
                    claim_type=item["claim_type"],
                    verification_status=item["verification_status"],
                    severity=item["severity"],
                    confidence=item["confidence"],
                    explanation=item["explanation"],
                    retrieved_evidence_text=item["retrieved_evidence_text"],
                    source_document_id=item["source_document_id"],
                    source_document_name=item["source_document_name"],
                    source_passage=item["source_passage"],
                    source_validity_date=item["source_validity_date"],
                    recommended_action=item["recommended_action"],
                    suggested_correction=item["suggested_correction"],
                )
                db.add(c)
                claims.append(c)
            db.commit()

    return [
        {
            "id": c.id,
            "claim_text": c.claim_text,
            "claim_type": c.claim_type,
            "verification_status": c.verification_status,
            "severity": c.severity,
            "confidence": c.confidence,
            "explanation": c.explanation,
            "source_document_name": c.source_document_name,
            "source_passage": c.source_passage,
            "source_validity_date": c.source_validity_date.isoformat() if c.source_validity_date else None,
            "suggested_correction": c.suggested_correction,
            "recommended_action": c.recommended_action,
        }
        for c in claims
    ]


@router.get("/graph/{submission_id}", summary="Get Evidence Intelligence Graph Payload")
def get_evidence_graph(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """
    Constructs an interactive evidence graph connecting:
    Submission -> Extracted Claims -> Approved Knowledge Documents & Facts.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    claims = db.query(ExtractedClaim).filter(
        ExtractedClaim.submission_id == submission_id,
        ExtractedClaim.organization_id == current_user.organization_id
    ).all()

    # If no claims yet, run auto extraction & verification
    if not claims:
        # Extract on the fly
        content_body = ""
        if submission.versions:
            content_body = submission.versions[-1].content_body
        if content_body:
            raw_claims = extract_factual_claims(content_body)
            verified = verify_claims_against_evidence(raw_claims, current_user.organization_id, db)
            for item in verified:
                c = ExtractedClaim(
                    id=str(uuid.uuid4()),
                    submission_id=submission_id,
                    organization_id=current_user.organization_id,
                    claim_text=item["claim_text"],
                    claim_type=item["claim_type"],
                    verification_status=item["verification_status"],
                    severity=item["severity"],
                    confidence=item["confidence"],
                    explanation=item["explanation"],
                    retrieved_evidence_text=item["retrieved_evidence_text"],
                    source_document_id=item["source_document_id"],
                    source_document_name=item["source_document_name"],
                    source_passage=item["source_passage"],
                    source_validity_date=item["source_validity_date"],
                    recommended_action=item["recommended_action"],
                    suggested_correction=item["suggested_correction"],
                )
                db.add(c)
                claims.append(c)
            db.commit()

    graph_data = build_evidence_graph_data(
        submission_id=submission.id,
        submission_title=submission.title,
        claims=claims,
        db=db
    )

    return graph_data


@router.post("/verify-text", summary="Real-time Evidence Verification for Draft Text")
def verify_text_claims(
    payload: Dict[str, str] = Body(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """Direct real-time evidence evaluation for the editor workspace."""
    text = payload.get("text", "")
    if not text:
        return {"claims": []}

    raw_claims = extract_factual_claims(text)
    verified = verify_claims_against_evidence(
        claims=raw_claims,
        organization_id=current_user.organization_id,
        db=db
    )

    return {
        "total_claims": len(verified),
        "claims": verified,
    }
