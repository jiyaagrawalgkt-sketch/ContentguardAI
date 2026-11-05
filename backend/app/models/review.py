import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class ReviewDecision(str, enum.Enum):
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ReviewComment(Base):
    __tablename__ = "review_comments"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    comment_text = Column(Text, nullable=False)
    is_internal_only = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="review_comments")
    reviewer = relationship("User", back_populates="review_comments")


class ApprovalRecord(Base):
    __tablename__ = "approval_records"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    decision = Column(String(30), nullable=False, index=True)  # approved, rejected, changes_requested
    feedback_reason = Column(Text, nullable=False)
    compliance_score_at_approval = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    submission = relationship("ContentSubmission", back_populates="approval_records")
    reviewer = relationship("User", back_populates="approval_records")
