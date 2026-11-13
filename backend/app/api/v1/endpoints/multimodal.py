import os
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Body
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_creator, require_reviewer, require_any_authenticated
from app.models.user import User
from app.models.submission import ContentSubmission, UploadedFile, ContentVersion, SubmissionStatus
from app.models.multimodal import VisualAnalysisReport
from app.models.brand_knowledge import BrandAsset, RestrictedTerm
from app.models.review import ReviewComment, ApprovalRecord
from app.models.publication import PublishedContent
from app.models.audit import AuditLog
from app.engine.multimodal_engine import analyze_visual_asset, generate_corrected_visual_asset

router = APIRouter()

IMAGE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "visual_assets")
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)


@router.post("/analyze", status_code=status.HTTP_201_CREATED, summary="Upload and Analyze Visual Brand Asset")
def analyze_visual_endpoint(
    file: UploadFile = File(...),
    submission_id: Optional[str] = Form(None),
    alt_text: Optional[str] = Form(None),
    title: Optional[str] = Form(None),
    current_user: User = Depends(require_creator),
    db: Session = Depends(get_db),
):
    """
    Multimodal Brand Intelligence analysis:
    - Dominant color extraction & brand palette distance
    - WCAG 2.1 optical contrast ratio & compliance level (AAA, AA, Fail)
    - OCR text extraction from visual banners & posters
    - Alt-text accessibility evaluation
    - Logo alignment & visual violation flagging
    """
    filename = file.filename or "image.png"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ["png", "jpg", "jpeg", "webp", "svg", "bmp"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported image format. Allowed formats: PNG, JPG, JPEG, WEBP, SVG"
        )

    file_bytes = file.file.read() if hasattr(file, "file") else file.read()
    if len(file_bytes) > 15 * 1024 * 1024:  # 15MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image size exceeds maximum 15MB limit"
        )

    # Save image securely
    safe_name = f"{uuid.uuid4().hex[:12]}_{filename}"
    file_path = os.path.join(IMAGE_UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # Resolve or create parent submission
    sub = None
    if submission_id:
        sub = db.query(ContentSubmission).filter(
            ContentSubmission.id == submission_id,
            ContentSubmission.organization_id == current_user.organization_id
        ).first()

    if not sub:
        sub_title = title.strip() if title else f"Visual Asset: {filename}"
        sub = ContentSubmission(
            id=str(uuid.uuid4()),
            organization_id=current_user.organization_id,
            creator_id=current_user.id,
            title=sub_title,
            category="social_media",
            target_platform="Web / Marketing Banner",
            status=SubmissionStatus.DRAFT.value,
        )
        db.add(sub)
        db.flush()

    # Get Organization Brand Asset for palette / logo comparison
    brand_asset = db.query(BrandAsset).filter(
        BrandAsset.organization_id == current_user.organization_id,
        BrandAsset.is_active == True
    ).first()

    # Run Multimodal Inspection Engine
    analysis_res = analyze_visual_asset(
        image_bytes=file_bytes,
        alt_text=alt_text,
        brand_asset=brand_asset
    )

    # If OCR extracted text, check for restricted terms
    ocr_text = analysis_res.get("ocr_extracted_text", "")
    if ocr_text:
        restricted_terms = db.query(RestrictedTerm).filter(
            RestrictedTerm.organization_id == current_user.organization_id,
            RestrictedTerm.is_active == True
        ).all()
        for rt in restricted_terms:
            if rt.term.lower() in ocr_text.lower():
                analysis_res["visual_issues"].append({
                    "type": "restricted_term_in_image",
                    "severity": rt.severity,
                    "title": f"Restricted Term Found in Graphic: '{rt.term}'",
                    "explanation": f"OCR identified restricted term '{rt.term}' embedded in the graphic. Reason: {rt.reason or 'Policy violation'}.",
                    "suggestion": f"Replace with approved alternative: '{rt.approved_replacement}'." if rt.approved_replacement else "Remove term from graphic."
                })

    # Save UploadedFile record
    uploaded_file = UploadedFile(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        original_filename=filename,
        stored_path=file_path,
        mime_type=file.content_type or f"image/{ext}",
        file_size_bytes=len(file_bytes),
        extracted_text=ocr_text,
        metadata_json={
            "width": analysis_res["image_width"],
            "height": analysis_res["image_height"],
            "aspect_ratio": analysis_res["aspect_ratio"],
        }
    )
    db.add(uploaded_file)
    db.flush()

    # Ensure submission has an active ContentVersion containing OCR text and asset metadata
    if not sub.versions:
        body_parts = [f"[Visual Brand Asset: {filename}]"]
        if ocr_text:
            body_parts.append(f"OCR Extracted Copy:\n{ocr_text}")
        if alt_text:
            body_parts.append(f"Accessibility Alt Text:\n{alt_text}")
        content_body = "\n\n".join(body_parts)

        initial_ver = ContentVersion(
            id=str(uuid.uuid4()),
            submission_id=sub.id,
            version_number=1,
            content_body=content_body,
            change_summary="Initial visual asset upload & optical analysis"
        )
        db.add(initial_ver)
        db.flush()
        sub.current_version_id = initial_ver.id

    if sub.status == SubmissionStatus.DRAFT.value:
        sub.status = SubmissionStatus.ANALYSIS_COMPLETE.value

    # Save VisualAnalysisReport
    report = VisualAnalysisReport(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        uploaded_file_id=uploaded_file.id,
        organization_id=current_user.organization_id,
        image_width=analysis_res["image_width"],
        image_height=analysis_res["image_height"],
        aspect_ratio=analysis_res["aspect_ratio"],
        dominant_colors=analysis_res["dominant_colors"],
        palette_match_score=analysis_res["palette_match_score"],
        palette_deviations=analysis_res["palette_deviations"],
        contrast_ratio=analysis_res["contrast_ratio"],
        wcag_compliance=analysis_res["wcag_compliance"],
        contrast_details=analysis_res["contrast_details"],
        alt_text_evaluation=analysis_res["alt_text_evaluation"],
        logo_status=analysis_res["logo_status"],
        logo_confidence=analysis_res["logo_confidence"],
        detected_logo_name=analysis_res["detected_logo_name"],
        ocr_extracted_text=ocr_text,
        ocr_character_count=len(ocr_text),
        ocr_confidence=analysis_res["ocr_confidence"],
        visual_score=analysis_res["visual_score"],
        visual_issues=analysis_res["visual_issues"],
    )
    db.add(report)

    # Record Audit Log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="VISUAL_ANALYSIS_COMPLETED",
        entity_type="visual_report",
        entity_id=report.id,
        details={
            "submission_id": sub.id,
            "filename": filename,
            "visual_score": report.visual_score,
            "wcag": report.wcag_compliance,
            "contrast_ratio": report.contrast_ratio,
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "submission_id": sub.id,
        "filename": filename,
        "dimensions": f"{report.image_width}x{report.image_height}",
        "aspect_ratio": report.aspect_ratio,
        "visual_score": report.visual_score,
        "wcag_compliance": report.wcag_compliance,
        "contrast_ratio": report.contrast_ratio,
        "contrast_details": report.contrast_details,
        "palette_match_score": report.palette_match_score,
        "dominant_colors": report.dominant_colors,
        "palette_deviations": report.palette_deviations,
        "alt_text_evaluation": report.alt_text_evaluation,
        "logo_status": report.logo_status,
        "ocr_extracted_text": report.ocr_extracted_text,
        "visual_issues": report.visual_issues,
        "review_status": report.review_status,
        "has_corrected_image": bool(report.corrected_image_path),
        "accepted_corrections": report.accepted_corrections or [],
        "rejected_corrections": report.rejected_corrections or [],
    }


@router.get("/reports/{report_id}", summary="Get Single Visual Analysis Report")
def get_visual_report(
    report_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()

    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual report not found")

    return {
        "report_id": report.id,
        "submission_id": report.submission_id,
        "dimensions": f"{report.image_width}x{report.image_height}",
        "aspect_ratio": report.aspect_ratio,
        "visual_score": report.visual_score,
        "wcag_compliance": report.wcag_compliance,
        "contrast_ratio": report.contrast_ratio,
        "contrast_details": report.contrast_details,
        "palette_match_score": report.palette_match_score,
        "dominant_colors": report.dominant_colors,
        "palette_deviations": report.palette_deviations,
        "alt_text_evaluation": report.alt_text_evaluation,
        "logo_status": report.logo_status,
        "ocr_extracted_text": report.ocr_extracted_text,
        "visual_issues": report.visual_issues,
        "review_status": report.review_status,
        "has_corrected_image": bool(report.corrected_image_path and os.path.exists(report.corrected_image_path)),
        "accepted_corrections": report.accepted_corrections or [],
        "rejected_corrections": report.rejected_corrections or [],
        "creator_notes": report.creator_notes,
        "reviewer_comments": report.reviewer_comments,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "is_published": report.is_published,
        "created_at": report.created_at.isoformat(),
    }


@router.get("/reports/{report_id}/image/{variant}", summary="Serve Visual Asset Image File")
def get_report_image(
    report_id: str,
    variant: str,  # 'original' or 'corrected'
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(VisualAnalysisReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    file_path = None
    if variant.lower() == "corrected":
        file_path = report.corrected_image_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Corrected image not found")
    else:
        if report.uploaded_file and report.uploaded_file.stored_path:
            file_path = report.uploaded_file.stored_path
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Original image not found")

    return FileResponse(file_path, media_type="image/png")


@router.post("/reports/{report_id}/findings/{finding_id}/decision", summary="Accept or Reject Individual Visual Correction")
def decide_visual_finding(
    report_id: str,
    finding_id: str,
    payload: Dict[str, str] = Body(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    decision = payload.get("decision", "").lower().strip()
    if decision not in ["accept", "reject", "reset"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be 'accept', 'reject', or 'reset'")

    accepted = set(report.accepted_corrections or [])
    rejected = set(report.rejected_corrections or [])

    if decision == "accept":
        accepted.add(finding_id)
        rejected.discard(finding_id)
    elif decision == "reject":
        rejected.add(finding_id)
        accepted.discard(finding_id)
    else:
        accepted.discard(finding_id)
        rejected.discard(finding_id)

    report.accepted_corrections = list(accepted)
    report.rejected_corrections = list(rejected)
    db.commit()

    return {
        "message": f"Finding '{finding_id}' marked as {decision}ed",
        "accepted_corrections": report.accepted_corrections,
        "rejected_corrections": report.rejected_corrections,
    }


@router.post("/reports/{report_id}/generate-corrected", summary="Auto-Generate Corrected Visual Asset")
def generate_corrected_visual_endpoint(
    report_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report or not report.uploaded_file:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report or source file not found")

    orig_path = report.uploaded_file.stored_path
    if not os.path.exists(orig_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source image file missing from server")

    brand_asset = db.query(BrandAsset).filter(
        BrandAsset.organization_id == current_user.organization_id,
        BrandAsset.is_active == True
    ).first()

    corrected_filename = f"{uuid.uuid4().hex[:12]}_corrected_{report.uploaded_file.original_filename}"
    corrected_path = os.path.join(IMAGE_UPLOAD_DIR, corrected_filename)

    res = generate_corrected_visual_asset(
        original_image_path=orig_path,
        output_path=corrected_path,
        accepted_corrections=report.accepted_corrections or ["contrast_enhancement"],
        brand_asset=brand_asset
    )

    # Save UploadedFile record for corrected asset
    corr_file = UploadedFile(
        id=str(uuid.uuid4()),
        submission_id=report.submission_id,
        original_filename=f"corrected_{report.uploaded_file.original_filename}",
        stored_path=corrected_path,
        mime_type="image/png",
        file_size_bytes=os.path.getsize(corrected_path),
        metadata_json={
            "width": res["width"],
            "height": res["height"],
            "is_corrected_version": True,
        }
    )
    db.add(corr_file)
    db.flush()

    report.corrected_file_id = corr_file.id
    report.corrected_image_path = corrected_path
    db.commit()

    return {
        "message": "Corrected visual asset generated successfully",
        "report_id": report.id,
        "has_corrected_image": True,
        "corrected_url": f"/multimodal/reports/{report.id}/image/corrected",
    }


@router.post("/reports/{report_id}/upload-corrected", summary="Upload Artist-Corrected Visual Asset")
def upload_corrected_visual_endpoint(
    report_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    file_bytes = file.file.read() if hasattr(file, "file") else file.read()
    filename = file.filename or "corrected.png"
    safe_name = f"{uuid.uuid4().hex[:12]}_user_corrected_{filename}"
    file_path = os.path.join(IMAGE_UPLOAD_DIR, safe_name)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    corr_file = UploadedFile(
        id=str(uuid.uuid4()),
        submission_id=report.submission_id,
        original_filename=filename,
        stored_path=file_path,
        mime_type=file.content_type or "image/png",
        file_size_bytes=len(file_bytes),
        metadata_json={"is_artist_corrected": True}
    )
    db.add(corr_file)
    db.flush()

    report.corrected_file_id = corr_file.id
    report.corrected_image_path = file_path
    db.commit()

    return {
        "message": "Replacement visual uploaded successfully",
        "report_id": report.id,
        "has_corrected_image": True,
    }


@router.post("/reports/{report_id}/submit-review", summary="Submit Visual Asset For Reviewer Approval")
def submit_visual_for_review(
    report_id: str,
    payload: Dict[str, str] = Body(...),
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    notes = payload.get("notes", "")
    report.creator_notes = notes
    report.review_status = "pending_review"

    # Also update submission status
    if report.submission:
        report.submission.status = SubmissionStatus.PENDING_REVIEW.value

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="VISUAL_SUBMITTED_FOR_REVIEW",
        entity_type="visual_report",
        entity_id=report.id,
        details={"notes": notes}
    )
    db.add(audit)
    db.commit()

    return {
        "message": "Visual asset submitted for reviewer governance check",
        "report_id": report.id,
        "review_status": report.review_status,
    }


@router.post("/reports/{report_id}/review-decision", summary="Reviewer Decision on Visual Asset")
def decide_visual_review(
    report_id: str,
    payload: Dict[str, str] = Body(...),
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    decision = payload.get("decision", "").lower().strip()
    comment = (payload.get("comment") or payload.get("comments") or "").strip()

    valid = {"approved": "approved", "rejected": "rejected", "changes_requested": "changes_requested"}
    if decision not in valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Decision must be 'approved', 'rejected', or 'changes_requested'")

    report.review_status = valid[decision]
    report.reviewer_comments = comment
    report.reviewed_at = datetime.now(timezone.utc)
    report.reviewed_by_user_id = current_user.id

    # Strictly separate approval from publishing:
    if decision == "approved":
        report.is_published = False  # Not published until explicit publishing action
        if report.submission:
            report.submission.status = SubmissionStatus.APPROVED.value
    elif decision == "changes_requested" and report.submission:
        report.submission.status = SubmissionStatus.CHANGES_REQUESTED.value
    elif decision == "rejected" and report.submission:
        report.submission.status = SubmissionStatus.REJECTED.value

    # Synchronize submission ReviewComment and ApprovalRecord
    if report.submission:
        comm_rec = ReviewComment(
            id=str(uuid.uuid4()),
            submission_id=report.submission.id,
            reviewer_id=current_user.id,
            comment_text=f"[Visual Asset Review] {comment}" if comment else f"[Visual Asset Review] Status updated to {decision}",
            is_internal_only=False
        )
        db.add(comm_rec)
        appr_rec = ApprovalRecord(
            id=str(uuid.uuid4()),
            submission_id=report.submission.id,
            reviewer_id=current_user.id,
            decision=decision,
            feedback_reason=comment,
            compliance_score_at_approval=report.visual_score
        )
        db.add(appr_rec)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action=f"VISUAL_REVIEW_{decision.upper()}",
        entity_type="visual_report",
        entity_id=report.id,
        details={"comment": comment, "decision": decision}
    )
    db.add(audit)
    db.commit()
    db.refresh(report)

    return {
        "report_id": report.id,
        "submission_id": report.submission_id,
        "dimensions": f"{report.image_width}x{report.image_height}",
        "aspect_ratio": report.aspect_ratio,
        "visual_score": report.visual_score,
        "wcag_compliance": report.wcag_compliance,
        "contrast_ratio": report.contrast_ratio,
        "contrast_details": report.contrast_details,
        "palette_match_score": report.palette_match_score,
        "dominant_colors": report.dominant_colors,
        "palette_deviations": report.palette_deviations,
        "alt_text_evaluation": report.alt_text_evaluation,
        "logo_status": report.logo_status,
        "ocr_extracted_text": report.ocr_extracted_text,
        "visual_issues": report.visual_issues,
        "review_status": report.review_status,
        "has_corrected_image": bool(report.corrected_image_path and os.path.exists(report.corrected_image_path)),
        "accepted_corrections": report.accepted_corrections or [],
        "rejected_corrections": report.rejected_corrections or [],
        "creator_notes": report.creator_notes,
        "reviewer_comments": report.reviewer_comments,
        "reviewed_at": report.reviewed_at.isoformat() if report.reviewed_at else None,
        "is_published": report.is_published,
        "reviewer": current_user.full_name,
        "message": f"Visual asset review recorded: {decision}",
    }


@router.post("/reports/{report_id}/publish", summary="Publish Approved Visual Brand Asset")
def publish_visual_report(
    report_id: str,
    current_user: User = Depends(require_reviewer),
    db: Session = Depends(get_db),
):
    """Publish an approved visual asset with live preview token generation."""
    report = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.id == report_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Visual report not found")

    if report.review_status != "approved":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot publish: visual asset review status is '{report.review_status}'. Asset must be approved before publishing."
        )

    sub = report.submission
    if sub and sub.status not in [SubmissionStatus.APPROVED.value, SubmissionStatus.PUBLISHED.value]:
        sub.status = SubmissionStatus.APPROVED.value

    report.is_published = True
    report.published_at = datetime.now(timezone.utc)

    token = None
    if sub:
        pub = db.query(PublishedContent).filter_by(submission_id=sub.id).first()
        token = pub.public_preview_token if pub else "pub_" + uuid.uuid4().hex
        ver = sub.versions[-1] if sub.versions else None
        snapshot = ver.content_body if ver else f"[Visual Brand Asset: {report.uploaded_file.original_filename if report.uploaded_file else 'Asset'}]"

        if not pub:
            pub = PublishedContent(
                id=str(uuid.uuid4()),
                submission_id=sub.id,
                public_preview_token=token,
                published_by=current_user.id,
                published_at=datetime.now(timezone.utc),
                final_content_snapshot=snapshot,
                public_access_enabled=True,
            )
            db.add(pub)
        else:
            pub.published_at = datetime.now(timezone.utc)
            pub.final_content_snapshot = snapshot
            pub.published_by = current_user.id
            pub.public_access_enabled = True

        sub.status = SubmissionStatus.PUBLISHED.value

    db.commit()

    return {
        "message": "Visual brand asset certified and published successfully",
        "report_id": report.id,
        "submission_id": sub.id if sub else None,
        "is_published": True,
        "published_at": report.published_at.isoformat(),
        "public_preview_token": token,
    }


@router.get("/reports/{report_id}/download-asset", summary="Download Certified Publication-Ready Asset")
def download_approved_visual(
    report_id: str,
    db: Session = Depends(get_db),
):
    report = db.query(VisualAnalysisReport).filter(VisualAnalysisReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")

    if not report.is_published and report.review_status != "approved":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Asset has not been certified and approved for publication")

    # Use corrected if available, otherwise original
    file_path = report.corrected_image_path or (report.uploaded_file.stored_path if report.uploaded_file else None)
    if not file_path or not os.path.exists(file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Certified file not found on server")

    filename = f"approved_{report.uploaded_file.original_filename if report.uploaded_file else 'visual_asset.png'}"
    return FileResponse(file_path, filename=filename, media_type="image/png")


@router.get("/submission/{submission_id}", summary="Get Visual Reports for Submission")
def get_submission_visual_reports(
    submission_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """Retrieve all multimodal visual audit reports associated with a submission."""
    reports = db.query(VisualAnalysisReport).filter(
        VisualAnalysisReport.submission_id == submission_id,
        VisualAnalysisReport.organization_id == current_user.organization_id
    ).all()

    return [
        {
            "report_id": r.id,
            "submission_id": r.submission_id,
            "dimensions": f"{r.image_width}x{r.image_height}",
            "aspect_ratio": r.aspect_ratio,
            "visual_score": r.visual_score,
            "wcag_compliance": r.wcag_compliance,
            "contrast_ratio": r.contrast_ratio,
            "contrast_details": r.contrast_details,
            "palette_match_score": r.palette_match_score,
            "dominant_colors": r.dominant_colors,
            "palette_deviations": r.palette_deviations,
            "alt_text_evaluation": r.alt_text_evaluation,
            "logo_status": r.logo_status,
            "ocr_extracted_text": r.ocr_extracted_text,
            "visual_issues": r.visual_issues,
            "review_status": r.review_status,
            "has_corrected_image": bool(r.corrected_image_path and os.path.exists(r.corrected_image_path)),
            "accepted_corrections": r.accepted_corrections or [],
            "rejected_corrections": r.rejected_corrections or [],
            "creator_notes": r.creator_notes,
            "reviewer_comments": r.reviewer_comments,
            "is_published": r.is_published,
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
