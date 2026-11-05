import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.permissions import require_reviewer
from app.models.user import User, UserRole
from app.models.submission import ContentSubmission, SubmissionStatus
from app.models.review import ReviewComment, ApprovalRecord, ReviewDecision
from app.models.audit import AuditLog
from app.schemas.submission import SubmissionListItem, SubmissionOut
from app.schemas.review import ReviewDecisionRequest, ApprovalRecordOut
from app.api.v1.endpoints.submissions import _format_submission_out

router = APIRouter()


@router.get("/queue", response_model=List[SubmissionListItem], summary="Reviewer Queue")
def get_review_queue(
    status_filter: Optional[str] = Query(None, description="Optional status filter"),
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Returns submissions awaiting review or filtered by status for the reviewer's organization.
    """
    query = db.query(ContentSubmission).filter(
        ContentSubmission.organization_id == current_user.organization_id
    )

    if isinstance(status_filter, str) and status_filter.lower() != "all":
        query = query.filter(ContentSubmission.status == status_filter.lower().strip())
    else:
        # Default active review queue
        query = query.filter(
            ContentSubmission.status.in_([
                SubmissionStatus.PENDING_REVIEW.value,
                SubmissionStatus.CHANGES_REQUESTED.value,
                SubmissionStatus.ANALYSIS_COMPLETE.value,
            ])
        )

    submissions = query.order_by(desc(ContentSubmission.updated_at)).all()

    items = []
    for s in submissions:
        latest_report = s.analysis_reports[-1] if s.analysis_reports else None
        items.append(
            SubmissionListItem(
                id=s.id,
                title=s.title,
                category=s.category,
                target_platform=s.target_platform,
                campaign_name=s.campaign_name,
                status=s.status,
                compliance_score=latest_report.compliance_score if latest_report else None,
                compliance_rating=latest_report.compliance_rating if latest_report else None,
                creator_name=s.creator.full_name if s.creator else "Unknown",
                version_count=len(s.versions),
                created_at=s.created_at,
                updated_at=s.updated_at,
            )
        )

    return items


@router.post("/{submission_id}/decide", response_model=SubmissionOut, summary="Submit Review Decision")
def decide_submission(
    submission_id: str,
    payload: ReviewDecisionRequest,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db)
):
    """
    Record review decision (approve, reject, or request changes) with real reviewer details and score.
    Enforces conflict of interest prevention: reviewers cannot approve their own submissions.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Conflict of interest prevention
    if submission.creator_id == current_user.id and current_user.role != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conflict of interest: Reviewers cannot approve or reject their own submissions"
        )

    decision_normalized = payload.decision.lower().strip()
    valid_decisions = {
        "approved": SubmissionStatus.APPROVED.value,
        "rejected": SubmissionStatus.REJECTED.value,
        "changes_requested": SubmissionStatus.CHANGES_REQUESTED.value,
    }

    if decision_normalized not in valid_decisions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid decision. Allowed values: {', '.join(valid_decisions.keys())}"
        )

    # Get actual compliance score at approval
    latest_report = submission.analysis_reports[-1] if submission.analysis_reports else None
    score_at_decision = latest_report.compliance_score if latest_report else 0.0

    # Record ReviewComment
    comment = ReviewComment(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        reviewer_id=current_user.id,
        comment_text=payload.comment,
        is_internal_only=False
    )
    db.add(comment)

    # Record ApprovalRecord
    record = ApprovalRecord(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        reviewer_id=current_user.id,
        decision=decision_normalized,
        feedback_reason=payload.comment,
        compliance_score_at_approval=score_at_decision
    )
    db.add(record)

    # Update Submission status
    submission.status = valid_decisions[decision_normalized]
    db.commit()
    db.refresh(submission)

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=f"REVIEW_{decision_normalized.upper()}",
        entity_type="content_submission",
        entity_id=submission.id,
        details={
            "decision": decision_normalized,
            "reviewer": current_user.full_name,
            "score": score_at_decision
        }
    )
    db.add(audit)
    db.commit()

    return _format_submission_out(submission)
