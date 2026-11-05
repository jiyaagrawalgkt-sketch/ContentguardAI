import uuid
import time
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.analysis import AnalysisReport, DetectedIssue, CorrectionSuggestion
from app.models.audit import AuditLog
from app.engine.gemini_analyzer import analyze_content
from pydantic import BaseModel, Field
from app.schemas.submission import ReportOut, DetectedIssueOut

router = APIRouter()


class IssueDismissRequest(BaseModel):
    reason: str = Field(..., min_length=2, max_length=255)


@router.post("/issues/{issue_id}/dismiss", summary="Dismiss Finding")
def dismiss_issue(
    issue_id: str,
    payload: IssueDismissRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    issue = db.query(DetectedIssue).filter(DetectedIssue.id == issue_id).first()
    if not issue:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Issue not found")
    
    if issue.report and issue.report.submission and issue.report.submission.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    issue.is_dismissed = True
    issue.dismiss_reason = payload.reason
    db.commit()

    return {"message": "Issue dismissed successfully", "id": issue.id, "dismiss_reason": payload.reason}


@router.post("/analyze/{submission_id}", response_model=ReportOut, summary="Run Content Analysis")
def run_analysis(
    submission_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Executes brand voice, restricted terminology, fact consistency, and claims analysis on the current draft version.
    """
    submission = db.query(ContentSubmission).filter(
        ContentSubmission.id == submission_id,
        ContentSubmission.organization_id == current_user.organization_id
    ).first()

    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Get current version
    current_version = None
    if submission.current_version_id:
        current_version = next((v for v in submission.versions if v.id == submission.current_version_id), None)
    if not current_version and submission.versions:
        current_version = submission.versions[-1]

    if not current_version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Submission has no content versions to analyze")

    start_time = time.time()
    submission.status = SubmissionStatus.ANALYZING.value
    db.commit()

    try:
        # Execute hybrid analysis engine
        issues, score, rating, counts, engine_mode = analyze_content(
            content=current_version.content_body,
            organization_id=submission.organization_id,
            db=db,
            category=submission.category,
            target_platform=submission.target_platform
        )
    except Exception as exc:
        submission.status = SubmissionStatus.DRAFT.value
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis engine execution failed: {str(exc)}"
        )
    duration_ms = int((time.time() - start_time) * 1000)

    # Build summary verdict
    if score >= 90:
        verdict = f"High brand compliance ({score:.0f}/100). Content aligns with voice guidelines and factual standards."
    elif score >= 75:
        verdict = f"Moderate compliance ({score:.0f}/100). Detected {len(issues)} item(s) requiring revision before approval."
    elif score >= 50:
        verdict = f"High compliance risk ({score:.0f}/100). Found {counts['critical']} critical and {counts['high']} high-severity violation(s)."
    else:
        verdict = f"Critical compliance breaches ({score:.0f}/100). Content contains unapproved guarantees or factual discrepancies."

    # Save report
    report = AnalysisReport(
        id=str(uuid.uuid4()),
        submission_id=submission.id,
        version_id=current_version.id,
        engine_mode=engine_mode,
        compliance_score=score,
        compliance_rating=rating,
        total_issues=len(issues),
        critical_count=counts["critical"],
        high_count=counts["high"],
        medium_count=counts["medium"],
        low_count=counts["low"],
        summary_verdict=verdict,
        execution_duration_ms=duration_ms
    )
    db.add(report)
    db.commit()

    issues_out = []
    # Save issues and suggestions
    for item in issues:
        category_val = item.get("category") or item.get("module") or "brand_voice"
        action_val = item.get("recommended_action") or "Replace"
        source_val = item.get("detection_source") or ("AI Contextual Analysis" if engine_mode == "hybrid_gemini" and item.get("confidence", 1.0) < 0.95 else "Rule Engine")

        issue = DetectedIssue(
            id=str(uuid.uuid4()),
            report_id=report.id,
            module=item["module"],
            category=category_val,
            severity=item["severity"],
            issue_type=item["issue_type"],
            matched_text=item["matched_text"],
            char_start=item.get("char_start"),
            char_end=item.get("char_end"),
            explanation=item["explanation"],
            guideline_reference=item["guideline_reference"],
            confidence=item.get("confidence", 1.0),
            recommended_action=action_val,
            detection_source=source_val,
            is_resolved=False,
            is_dismissed=False
        )
        db.add(issue)
        db.commit()

        sugg = None
        if item.get("suggested_replacement"):
            sugg = CorrectionSuggestion(
                id=str(uuid.uuid4()),
                issue_id=issue.id,
                original_text=item["matched_text"],
                suggested_replacement=item["suggested_replacement"],
                rationale=item.get("rationale", "Recommended brand correction"),
                is_accepted=False
            )
            db.add(sugg)
            db.commit()

        issues_out.append(
            DetectedIssueOut(
                id=issue.id,
                module=issue.module,
                category=issue.category,
                severity=issue.severity,
                issue_type=issue.issue_type,
                matched_text=issue.matched_text,
                char_start=issue.char_start,
                char_end=issue.char_end,
                explanation=issue.explanation,
                guideline_reference=issue.guideline_reference,
                confidence=issue.confidence,
                recommended_action=issue.recommended_action,
                detection_source=issue.detection_source,
                suggested_replacement=sugg.suggested_replacement if sugg else None,
                rationale=sugg.rationale if sugg else None,
                is_resolved=issue.is_resolved,
                is_dismissed=issue.is_dismissed,
                dismiss_reason=issue.dismiss_reason
            )
        )

    submission.status = SubmissionStatus.ANALYSIS_COMPLETE.value
    db.commit()

    # Record audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="ANALYSIS_RUN",
        entity_type="analysis_report",
        entity_id=report.id,
        details={"score": score, "total_issues": len(issues), "engine": engine_mode}
    )
    db.add(audit)
    db.commit()

    return ReportOut(
        id=report.id,
        version_id=report.version_id,
        engine_mode=report.engine_mode,
        compliance_score=report.compliance_score,
        compliance_rating=report.compliance_rating,
        total_issues=report.total_issues,
        critical_count=report.critical_count,
        high_count=report.high_count,
        medium_count=report.medium_count,
        low_count=report.low_count,
        summary_verdict=report.summary_verdict,
        issues=issues_out,
        created_at=report.created_at
    )
