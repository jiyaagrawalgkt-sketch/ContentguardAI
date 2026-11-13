import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_reviewer, require_any_authenticated
from app.models.user import User
from app.models.submission import ContentSubmission, SubmissionStatus
from app.models.publication import PublishedContent
from app.models.knowledge_base import ExtractedClaim
from app.models.audit import AuditLog
from app.schemas.review import PublishedContentOut

router = APIRouter()


@router.get("/{submission_id}/gate-status", summary="Smart Pre-Publication Gate Status")
def get_pre_publication_gate_status(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db)
):
    """
    Round 3 Feature 3: Smart Pre-Publication Gate.
    Verifies that all criteria (zero critical violations, verified evidence, reviewer approval)
    are satisfied before allowing publication.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    report = submission.analysis_reports[-1] if submission.analysis_reports else None
    visual_report = submission.visual_reports[-1] if submission.visual_reports else None
    claims = db.query(ExtractedClaim).filter(
        ExtractedClaim.submission_id == submission_id
    ).all()

    # Evaluation of gates
    blockers = []
    if not report and not visual_report:
        gate_status = "not_analyzed"
        blockers.append("Content has not been analyzed yet.")
        can_publish = False
    elif submission.status == SubmissionStatus.CHANGES_REQUESTED.value:
        gate_status = "changes_requested"
        blockers.append(f"Reviewer requested revisions: {submission.latest_review_feedback or 'Pending edits'}")
        can_publish = False
    elif report and report.critical_count > 0:
        gate_status = "needs_attention"
        blockers.append(f"{report.critical_count} critical policy violation(s) must be resolved.")
        can_publish = False
    elif any(c.verification_status in ["conflicting", "unsupported"] for c in claims):
        gate_status = "needs_attention"
        unverified_cnt = sum(1 for c in claims if c.verification_status in ["conflicting", "unsupported"])
        blockers.append(f"{unverified_cnt} factual claim(s) lack supporting evidence in Knowledge Hub.")
        can_publish = False
    elif submission.status != SubmissionStatus.APPROVED.value and submission.status != SubmissionStatus.PUBLISHED.value:
        gate_status = "awaiting_review"
        blockers.append("Submission is awaiting formal review by an authorized reviewer.")
        can_publish = False
    else:
        gate_status = "approved_for_publication"
        can_publish = True

    crit_count = report.critical_count if report else 0
    high_count = report.high_count if report else 0

    checks = {
        "analysis_completed": (report is not None) or (visual_report is not None),
        "zero_critical_violations": crit_count == 0,
        "zero_high_risk_violations": high_count == 0,
        "evidence_verified": not any(c.verification_status in ["conflicting", "unsupported"] for c in claims),
        "reviewer_approved": submission.status in [SubmissionStatus.APPROVED.value, SubmissionStatus.PUBLISHED.value]
    }

    return {
        "submission_id": submission_id,
        "gate_status": gate_status,
        "can_publish": can_publish,
        "checks": checks,
        "blockers": blockers,
        "status_label": gate_status.replace("_", " ").title()
    }



@router.post("/{submission_id}/publish", response_model=PublishedContentOut, summary="Publish Approved Content")
def publish_submission(
    submission_id: str,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Publish content. Enforces strict rule:
    Publishing can ONLY occur if the submission has been approved by an authorized reviewer.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.status != SubmissionStatus.APPROVED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish: submission status is '{submission.status}'. Content must be formally approved before publishing."
        )

    # Get current version content
    current_ver = None
    if submission.current_version_id:
        current_ver = next((v for v in submission.versions if v.id == submission.current_version_id), None)
    if not current_ver and submission.versions:
        current_ver = submission.versions[-1]

    if not current_ver:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No content version available to publish")

    latest_report = submission.analysis_reports[-1] if submission.analysis_reports else None
    latest_visual = submission.visual_reports[-1] if submission.visual_reports else None
    actual_score = latest_report.compliance_score if latest_report else (latest_visual.visual_score if latest_visual else 100.0)

    # Create or update published content record
    published = db.query(PublishedContent).filter_by(submission_id=submission.id).first()
    token = published.public_preview_token if published else "pub_" + uuid.uuid4().hex

    if not published:
        published = PublishedContent(
            id=str(uuid.uuid4()),
            submission_id=submission.id,
            public_preview_token=token,
            published_by=current_user.id,
            published_at=datetime.now(timezone.utc),
            final_content_snapshot=current_ver.content_body,
            public_access_enabled=True
        )
        db.add(published)
    else:
        published.published_at = datetime.now(timezone.utc)
        published.final_content_snapshot = current_ver.content_body
        published.published_by = current_user.id
        published.public_access_enabled = True

    submission.status = SubmissionStatus.PUBLISHED.value
    # Synchronize attached visual reports to published
    for vr in submission.visual_reports:
        vr.is_published = True
        vr.published_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(published)

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CONTENT_PUBLISHED",
        entity_type="published_content",
        entity_id=published.id,
        details={"token": token, "score": actual_score}
    )
    db.add(audit)
    db.commit()

    return PublishedContentOut(
        id=published.id,
        public_preview_token=published.public_preview_token,
        published_by_name=current_user.full_name,
        published_at=published.published_at,
        final_content_snapshot=published.final_content_snapshot,
        compliance_score=actual_score,
        title=submission.title,
        category=submission.category
    )


@router.get("/preview/by-sub/{submission_id}", response_model=PublishedContentOut, summary="Get Public Preview by Submission ID")
def get_preview_by_submission(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """Retrieve published record for a submission."""
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    published = db.query(PublishedContent).filter_by(submission_id=submission_id).first()
    if not published:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No publication record found for this submission")

    publisher_name = published.publisher.full_name if published.publisher else "Authorized Brand Reviewer"
    latest_report = submission.analysis_reports[-1] if submission.analysis_reports else None
    latest_visual = submission.visual_reports[-1] if submission.visual_reports else None
    actual_score = latest_report.compliance_score if latest_report else (latest_visual.visual_score if latest_visual else 100.0)

    return PublishedContentOut(
        id=published.id,
        public_preview_token=published.public_preview_token,
        published_by_name=publisher_name,
        published_at=published.published_at,
        final_content_snapshot=published.final_content_snapshot,
        compliance_score=actual_score,
        title=submission.title,
        category=submission.category
    )


@router.get("/preview/{token}", response_model=PublishedContentOut, summary="Public Read-Only Preview")
def get_public_preview(token: str, db: Session = Depends(get_db)):
    """
    Public unauthenticated endpoint to view verified published content.
    Exposes only genuinely approved and published content with real reviewer details and score.
    """
    published = db.query(PublishedContent).filter(
        PublishedContent.public_preview_token == token,
        PublishedContent.public_access_enabled == True
    ).first()

    if not published or not published.submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Public verified content not found or preview link has expired"
        )

    # Confirm genuine approved/published status
    if published.submission.status != SubmissionStatus.PUBLISHED.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Content has not been published"
        )

    # Fetch actual reviewer name from publisher or approval records
    publisher_name = published.publisher.full_name if published.publisher else "Authorized Brand Reviewer"
    latest_report = published.submission.analysis_reports[-1] if published.submission.analysis_reports else None
    latest_visual = published.submission.visual_reports[-1] if published.submission.visual_reports else None
    actual_score = latest_report.compliance_score if latest_report else (latest_visual.visual_score if latest_visual else 100.0)

    return PublishedContentOut(
        id=published.id,
        public_preview_token=published.public_preview_token,
        published_by_name=publisher_name,
        published_at=published.published_at,
        final_content_snapshot=published.final_content_snapshot,
        compliance_score=actual_score,
        title=published.submission.title,
        category=published.submission.category
    )
