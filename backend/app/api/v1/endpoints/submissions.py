import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.permissions import get_current_user, require_creator
from app.models.user import User, UserRole
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.analysis import AnalysisReport
from app.models.audit import AuditLog
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionUpdateContent,
    SubmissionOut,
    SubmissionListItem,
    VersionOut,
    ReportOut,
    DetectedIssueOut,
)

router = APIRouter()


def _format_report_out(report: Optional[AnalysisReport]) -> Optional[ReportOut]:
    if not report:
        return None

    issues_out = []
    for issue in report.issues:
        first_sugg = issue.suggestions[0] if issue.suggestions else None
        issues_out.append(
            DetectedIssueOut(
                id=issue.id,
                module=issue.module,
                category=getattr(issue, "category", issue.module) or "brand_voice",
                severity=issue.severity,
                issue_type=issue.issue_type,
                matched_text=issue.matched_text,
                char_start=issue.char_start,
                char_end=issue.char_end,
                explanation=issue.explanation,
                guideline_reference=issue.guideline_reference,
                confidence=issue.confidence,
                recommended_action=getattr(issue, "recommended_action", "Replace") or "Replace",
                detection_source=getattr(issue, "detection_source", "Rule Engine") or "Rule Engine",
                suggested_replacement=first_sugg.suggested_replacement if first_sugg else None,
                rationale=first_sugg.rationale if first_sugg else None,
                is_resolved=issue.is_resolved,
                is_dismissed=getattr(issue, "is_dismissed", False) or False,
                dismiss_reason=getattr(issue, "dismiss_reason", None),
            )
        )

    return ReportOut(
        id=report.id,
        version_id=report.version_id,
        engine_mode=report.engine_mode,
        compliance_score=report.compliance_score,
        compliance_rating=report.compliance_rating,
        brand_compliance_score=getattr(report, "brand_compliance_score", 100.0),
        evidence_confidence_score=getattr(report, "evidence_confidence_score", 100.0),
        content_quality_score=getattr(report, "content_quality_score", 100.0),
        publication_risk=getattr(report, "publication_risk", "low"),
        score_breakdown=getattr(report, "score_breakdown", None),
        total_issues=report.total_issues,
        critical_count=report.critical_count,
        high_count=report.high_count,
        medium_count=report.medium_count,
        low_count=report.low_count,
        summary_verdict=report.summary_verdict,
        issues=issues_out,
        created_at=report.created_at,
    )


def _format_submission_out(submission: ContentSubmission) -> SubmissionOut:
    current_content = ""
    # Find current version
    current_ver = None
    if submission.current_version_id:
        current_ver = next((v for v in submission.versions if v.id == submission.current_version_id), None)
    if not current_ver and submission.versions:
        current_ver = submission.versions[-1]

    if current_ver:
        current_content = current_ver.content_body

    latest_report = None
    if submission.analysis_reports:
        latest_report = sorted(submission.analysis_reports, key=lambda r: r.created_at)[-1]

    latest_review = None
    if submission.approval_records:
        latest_review = sorted(submission.approval_records, key=lambda r: r.created_at)[-1]

    return SubmissionOut(
        id=submission.id,
        title=submission.title,
        category=submission.category,
        target_platform=submission.target_platform,
        campaign_name=submission.campaign_name,
        description=submission.description,
        status=submission.status,
        current_version_id=submission.current_version_id,
        current_content=current_content,
        creator_id=submission.creator_id,
        creator_name=submission.creator.full_name if submission.creator else "Unknown",
        versions=[
            VersionOut(
                id=v.id,
                version_number=v.version_number,
                content_body=v.content_body,
                change_summary=v.change_summary,
                created_at=v.created_at,
            )
            for v in submission.versions
        ],
        latest_report=_format_report_out(latest_report),
        latest_review_feedback=latest_review.feedback_reason if latest_review else None,
        latest_reviewer_name=latest_review.reviewer.full_name if (latest_review and latest_review.reviewer) else None,
        created_at=submission.created_at,
        updated_at=submission.updated_at,
    )


@router.post("/", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED, summary="Create Text Submission")
def create_submission(
    payload: SubmissionCreate,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Creates a new content submission with Version 1."""
    submission = ContentSubmission(
        id=str(uuid.uuid4()),
        organization_id=current_user.organization_id,
        creator_id=current_user.id,
        title=payload.title,
        category=payload.category,
        target_platform=payload.target_platform,
        campaign_name=payload.campaign_name,
        description=payload.description,
        status=SubmissionStatus.DRAFT.value,
    )
    db.add(submission)
    db.commit()

    version1 = ContentVersion(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        version_number=1,
        content_body=payload.content,
        change_summary="Initial submission draft",
        created_by=current_user.id,
    )
    db.add(version1)
    db.commit()

    submission.current_version_id = version1.id
    db.commit()
    db.refresh(submission)

    # Record audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="SUBMISSION_CREATED",
        entity_type="content_submission",
        entity_id=submission.id,
        details={"title": submission.title, "category": submission.category}
    )
    db.add(audit)
    db.commit()

    return _format_submission_out(submission)


@router.get("/", response_model=List[SubmissionListItem], summary="List Submissions")
def list_submissions(
    status_filter: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List submissions.
    Creators see their own submissions.
    Reviewers and Admins see all submissions in the organization.
    """
    query = db.query(ContentSubmission).filter(
        ContentSubmission.organization_id == current_user.organization_id
    )

    if current_user.role == UserRole.CREATOR.value:
        query = query.filter(ContentSubmission.creator_id == current_user.id)

    if isinstance(status_filter, str) and status_filter:
        query = query.filter(ContentSubmission.status == status_filter)

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


@router.get("/{id}", response_model=SubmissionOut, summary="Get Submission Detail")
def get_submission(
    id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retrieve detailed submission record including all versions and the latest analysis report."""
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Creators can only view their own submissions
    if current_user.role == UserRole.CREATOR.value and submission.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    return _format_submission_out(submission)


@router.put("/{id}/content", response_model=SubmissionOut, summary="Update Content & Create New Version")
def update_submission_content(
    id: str,
    payload: SubmissionUpdateContent,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Saves edited content as a new sequential version."""
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role == UserRole.CREATOR.value and submission.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if submission.status == SubmissionStatus.PUBLISHED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Published content cannot be edited directly")

    next_version_num = len(submission.versions) + 1
    new_version = ContentVersion(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        version_number=next_version_num,
        content_body=payload.content,
        change_summary=payload.change_summary or f"Version {next_version_num} update",
        created_by=current_user.id,
    )
    db.add(new_version)
    db.commit()

    submission.current_version_id = new_version.id
    # If changes were requested, editing moves back to draft
    if submission.status in [SubmissionStatus.CHANGES_REQUESTED.value, SubmissionStatus.PENDING_REVIEW.value]:
        submission.status = SubmissionStatus.DRAFT.value

    db.commit()
    db.refresh(submission)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="CONTENT_UPDATED",
        entity_type="content_submission",
        entity_id=submission.id,
        details={"version": next_version_num, "summary": payload.change_summary}
    )
    db.add(audit)
    db.commit()

    return _format_submission_out(submission)


@router.post("/{id}/submit-review", response_model=SubmissionOut, summary="Submit Content for Review")
def submit_for_review(
    id: str,
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db)
):
    """Creator transitions content into the reviewer queue."""
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if current_user.role == UserRole.CREATOR.value and submission.creator_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if submission.status == SubmissionStatus.PUBLISHED.value:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Content is already published")

    submission.status = SubmissionStatus.PENDING_REVIEW.value
    db.commit()
    db.refresh(submission)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="SUBMITTED_FOR_REVIEW",
        entity_type="content_submission",
        entity_id=submission.id,
        details={"title": submission.title}
    )
    db.add(audit)
    db.commit()

    return _format_submission_out(submission)


@router.get("/campaigns/{campaign_name}/consistency", summary="Campaign Cross-Submission Consistency Checker")
def check_campaign_consistency(
    campaign_name: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Round 3 Feature 6: Compares multiple content submissions within the same campaign
    to detect conflicting numerical claims, divergent product metrics, and inconsistent terminology.
    """
    clean_camp = campaign_name.strip()
    subs = db.query(ContentSubmission).filter(
        ContentSubmission.organization_id == current_user.organization_id,
        ContentSubmission.campaign_name == clean_camp
    ).all()

    if not subs:
        return {
            "campaign_name": clean_camp,
            "submissions_count": 0,
            "consistency_score": 100.0,
            "status": "No submissions found for this campaign.",
            "inconsistencies": []
        }

    # Gather claims and latest copy across submissions
    items = []
    from app.engine.evidence_engine import extract_factual_claims
    import re

    for s in subs:
        content_body = ""
        if s.current_version_id:
            cv = next((v for v in s.versions if v.id == s.current_version_id), None)
            if cv:
                content_body = cv.content_body
        if not content_body and s.versions:
            content_body = s.versions[-1].content_body

        claims = extract_factual_claims(content_body) if content_body else []
        items.append({
            "id": s.id,
            "title": s.title,
            "category": s.category,
            "content": content_body,
            "claims": claims
        })

    inconsistencies = []
    # 1. Compare numerical claims across submissions
    metrics_by_topic: dict = {}
    for sub in items:
        for c in sub["claims"]:
            c_text = c["claim_text"].lower()
            # Normalize key
            key = None
            if "uptime" in c_text or "%" in c_text:
                key = "Availability / SLA Metric"
            elif "$" in c_text or "arr" in c_text:
                key = "Pricing / Revenue Metric"
            elif "latency" in c_text or "ms" in c_text:
                key = "Performance / Latency Metric"

            if key:
                if key not in metrics_by_topic:
                    metrics_by_topic[key] = []
                metrics_by_topic[key].append({
                    "submission_id": sub["id"],
                    "submission_title": sub["title"],
                    "claim_text": c["claim_text"],
                    "sentence": c.get("sentence", "")
                })

    # Check for discrepancies in the same metric topic
    for topic, occurrences in metrics_by_topic.items():
        unique_claims = {occ["claim_text"].strip().lower() for occ in occurrences}
        if len(unique_claims) > 1:
            inconsistencies.append({
                "metric_category": topic,
                "discrepancy": f"Conflicting values detected: {', '.join(unique_claims)}",
                "affected_submissions": occurrences,
                "severity": "high",
                "recommendation": f"Standardize on the organization approved specification for {topic}."
            })

    # Compute consistency score
    consistency_score = max(0.0, 100.0 - (len(inconsistencies) * 20.0))

    return {
        "campaign_name": clean_camp,
        "submissions_count": len(subs),
        "consistency_score": consistency_score,
        "status": "Consistent" if not inconsistencies else f"{len(inconsistencies)} Inconsistency Detected",
        "inconsistencies": inconsistencies
    }

