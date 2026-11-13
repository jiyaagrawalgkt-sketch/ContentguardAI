import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class WCAGComplianceLevel(str, enum.Enum):
    AAA_PASS = "AAA_PASS"
    AA_PASS = "AA_PASS"
    FAIL = "FAIL"


class LogoMatchStatus(str, enum.Enum):
    MATCHED = "matched"
    MISMATCHED = "mismatched"
    OUTDATED = "outdated"
    MISSING = "missing"
    NOT_APPLICABLE = "not_applicable"


class VisualAnalysisReport(Base):
    __tablename__ = "visual_analysis_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    uploaded_file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Geometry & Dimensions
    image_width = Column(Integer, default=0, nullable=False)
    image_height = Column(Integer, default=0, nullable=False)
    aspect_ratio = Column(String(20), nullable=True)

    # Color Palette Analysis
    dominant_colors = Column(JSON, nullable=True)  # List of {"hex": "#...", "percent": 45.2, "rgb": [..]}
    palette_match_score = Column(Float, default=100.0, nullable=False)  # 0.0 to 100.0
    palette_deviations = Column(JSON, nullable=True)  # Details of off-brand colors detected

    # Contrast & Accessibility (WCAG 2.1)
    contrast_ratio = Column(Float, default=21.0, nullable=False)  # e.g., 4.5, 7.0, 2.1
    wcag_compliance = Column(String(20), default=WCAGComplianceLevel.AA_PASS.value, nullable=False)
    contrast_details = Column(JSON, nullable=True)  # fg, bg, ratio, rating
    alt_text_evaluation = Column(JSON, nullable=True)  # {"provided_alt": "...", "score": 85, "verdict": "Clear"}

    # Logo & Visual Identity Verification
    logo_status = Column(String(30), default=LogoMatchStatus.NOT_APPLICABLE.value, nullable=False)
    logo_confidence = Column(Float, default=1.0, nullable=False)
    detected_logo_name = Column(String(255), nullable=True)
    logo_findings = Column(JSON, nullable=True)

    # OCR Extracted Content
    ocr_extracted_text = Column(Text, nullable=True)
    ocr_character_count = Column(Integer, default=0, nullable=False)
    ocr_confidence = Column(Float, default=1.0, nullable=False)

    # Aggregated Visual Violations
    visual_score = Column(Float, default=100.0, nullable=False)
    visual_issues = Column(JSON, nullable=True)  # List of {type, severity, title, explanation, suggestion, region}

    # Visual Workflow & Approval Extension
    corrected_file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True)
    corrected_image_path = Column(String(500), nullable=True)
    corrected_image_url = Column(String(500), nullable=True)
    post_correction_verification = Column(JSON, nullable=True)  # Independent post-correction audit details
    review_status = Column(String(30), default="draft", nullable=False)  # draft, pending_review, approved, rejected, changes_requested
    accepted_corrections = Column(JSON, default=list, nullable=True)
    rejected_corrections = Column(JSON, default=list, nullable=True)
    creator_notes = Column(Text, nullable=True)
    reviewer_comments = Column(Text, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by_user_id = Column(String(36), nullable=True)
    is_published = Column(Boolean, default=False, nullable=False)
    published_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="visual_reports")
    uploaded_file = relationship("UploadedFile", foreign_keys=[uploaded_file_id])
    corrected_file = relationship("UploadedFile", foreign_keys=[corrected_file_id])
