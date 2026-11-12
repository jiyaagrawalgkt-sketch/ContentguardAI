import os
import uuid
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.permissions import get_current_user, require_creator, require_any_authenticated
from app.models.user import User
from app.models.submission import ContentSubmission, UploadedFile, ContentVersion, SubmissionStatus
from app.models.multimodal import VisualAnalysisReport
from app.models.brand_knowledge import BrandAsset, RestrictedTerm
from app.models.audit import AuditLog
from app.engine.multimodal_engine import analyze_visual_asset

router = APIRouter()

IMAGE_UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "visual_assets")
os.makedirs(IMAGE_UPLOAD_DIR, exist_ok=True)


@router.post("/analyze", status_code=status.HTTP_201_CREATED, summary="Upload and Analyze Visual Brand Asset")
async def analyze_visual_endpoint(
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

    file_bytes = await file.read()
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
    }


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
            "created_at": r.created_at.isoformat(),
        }
        for r in reports
    ]
