import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class EngineMode(str, enum.Enum):
    HYBRID_GEMINI = "hybrid_gemini"
    DETERMINISTIC_FALLBACK = "deterministic_fallback"


class ComplianceRating(str, enum.Enum):
    COMPLIANT = "compliant"
    NEEDS_REVIEW = "needs_review"
    HIGH_RISK = "high_risk"
    CRITICAL_VIOLATIONS = "critical_violations"


class IssueCategory(str, enum.Enum):
    CONFIDENTIALITY = "confidentiality"
    PRIVACY = "privacy"
    MISLEADING_CLAIM = "misleading_claim"
    UNNECESSARY_CONTENT = "unnecessary_content"
    BRAND_VOICE = "brand_voice"
    SECURITY_TECHNICAL = "security_technical"


class IssueModule(str, enum.Enum):
    BRAND_VOICE = "brand_voice"
    FACT_CHECKER = "fact_checker"
    RESTRICTED_LANGUAGE = "restricted_language"
    MARKETING_CLAIM = "marketing_claim"
    CONFIDENTIALITY = "confidentiality"
    PRIVACY = "privacy"
    SECURITY_TECHNICAL = "security_technical"
    UNNECESSARY_CONTENT = "unnecessary_content"
    VISUAL_BRAND = "visual_brand"
    ACCESSIBILITY = "accessibility"


class IssueSeverity(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_id = Column(String(36), ForeignKey("content_versions.id", ondelete="CASCADE"), nullable=False, index=True)
    engine_mode = Column(String(30), default=EngineMode.DETERMINISTIC_FALLBACK.value, nullable=False)
    compliance_score = Column(Float, nullable=False)
    compliance_rating = Column(String(30), default=ComplianceRating.NEEDS_REVIEW.value, nullable=False, index=True)
    brand_compliance_score = Column(Float, nullable=True, default=100.0)
    evidence_confidence_score = Column(Float, nullable=True, default=100.0)
    content_quality_score = Column(Float, nullable=True, default=100.0)
    publication_risk = Column(String(30), nullable=True, default="low")
    score_breakdown = Column(JSON, nullable=True)
    total_issues = Column(Integer, default=0, nullable=False)
    critical_count = Column(Integer, default=0, nullable=False)
    high_count = Column(Integer, default=0, nullable=False)
    medium_count = Column(Integer, default=0, nullable=False)
    low_count = Column(Integer, default=0, nullable=False)
    summary_verdict = Column(Text, nullable=True)
    raw_model_response = Column(JSON, nullable=True)
    execution_duration_ms = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="analysis_reports")
    version = relationship("ContentVersion", back_populates="analysis_reports")
    issues = relationship("DetectedIssue", back_populates="report", cascade="all, delete-orphan")


class DetectedIssue(Base):
    __tablename__ = "detected_issues"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id = Column(String(36), ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False, index=True)
    module = Column(String(30), nullable=False, index=True)
    category = Column(String(50), default=IssueCategory.BRAND_VOICE.value, nullable=True, index=True)
    severity = Column(String(20), nullable=False, index=True)
    issue_type = Column(String(100), nullable=False)
    matched_text = Column(Text, nullable=False)
    char_start = Column(Integer, nullable=True)
    char_end = Column(Integer, nullable=True)
    explanation = Column(Text, nullable=False)
    guideline_reference = Column(String(255), nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    recommended_action = Column(String(30), default="Replace", nullable=True)
    correction_type = Column(String(30), default="REPLACE", nullable=True)
    suggested_replacement = Column(Text, nullable=True)
    detection_source = Column(String(50), default="Rule Engine", nullable=True)
    is_resolved = Column(Boolean, default=False, nullable=False)
    is_dismissed = Column(Boolean, default=False, nullable=False)
    dismiss_reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    report = relationship("AnalysisReport", back_populates="issues")
    suggestions = relationship("CorrectionSuggestion", back_populates="issue", cascade="all, delete-orphan")


class CorrectionSuggestion(Base):
    __tablename__ = "correction_suggestions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    issue_id = Column(String(36), ForeignKey("detected_issues.id", ondelete="CASCADE"), nullable=False, index=True)
    original_text = Column(Text, nullable=False)
    suggested_replacement = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    is_accepted = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    issue = relationship("DetectedIssue", back_populates="suggestions")
