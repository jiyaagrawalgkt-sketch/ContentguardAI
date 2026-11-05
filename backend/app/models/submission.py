import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class SubmissionStatus(str, enum.Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    ANALYZING = "analyzing"
    ANALYSIS_COMPLETE = "analysis_complete"
    PENDING_REVIEW = "pending_review"
    CHANGES_REQUESTED = "changes_requested"
    REJECTED = "rejected"
    APPROVED = "approved"
    PUBLISHED = "published"


class ContentCategory(str, enum.Enum):
    SOCIAL_MEDIA = "social_media"
    ADVERTISEMENT = "advertisement"
    MARKETING_EMAIL = "marketing_email"
    BLOG = "blog"
    WEBSITE = "website"
    BUSINESS_DOCUMENT = "business_document"


class ContentSubmission(Base):
    __tablename__ = "content_submissions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    creator_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    category = Column(String(50), default=ContentCategory.MARKETING_EMAIL.value, nullable=False, index=True)
    target_platform = Column(String(100), nullable=True)  # LinkedIn, Landing Page, Google Ads, etc.
    campaign_name = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    status = Column(String(30), default=SubmissionStatus.DRAFT.value, nullable=False, index=True)
    current_version_id = Column(String(36), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="submissions")
    creator = relationship("User", back_populates="submissions", foreign_keys=[creator_id])
    uploaded_files = relationship("UploadedFile", back_populates="submission", cascade="all, delete-orphan")
    versions = relationship("ContentVersion", back_populates="submission", cascade="all, delete-orphan", order_by="ContentVersion.version_number")
    analysis_reports = relationship("AnalysisReport", back_populates="submission", cascade="all, delete-orphan", order_by="AnalysisReport.created_at")
    review_comments = relationship("ReviewComment", back_populates="submission", cascade="all, delete-orphan")
    approval_records = relationship("ApprovalRecord", back_populates="submission", cascade="all, delete-orphan")
    published_content = relationship("PublishedContent", back_populates="submission", uselist=False, cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=False)
    stored_path = Column(String(500), nullable=False)
    mime_type = Column(String(100), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)  # Pages, dimensions, OCR confidence
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="uploaded_files")


class ContentVersion(Base):
    __tablename__ = "content_versions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    version_number = Column(Integer, nullable=False)
    content_body = Column(Text, nullable=False)
    change_summary = Column(String(255), nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="versions")
    analysis_reports = relationship("AnalysisReport", back_populates="version", cascade="all, delete-orphan")
