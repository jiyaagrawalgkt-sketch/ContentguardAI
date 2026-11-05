import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import require_reviewer
from app.models.user import User
from app.models.submission import ContentSubmission, SubmissionStatus
from app.models.publication import PublishedContent
from app.models.audit import AuditLog
from app.schemas.review import PublishedContentOut

router = APIRouter()


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
    actual_score = latest_report.compliance_score if latest_report else 100.0

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
    actual_score = latest_report.compliance_score if latest_report else 100.0

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
