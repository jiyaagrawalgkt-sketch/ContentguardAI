import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class PublishedContent(Base):
    __tablename__ = "published_content"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), unique=True, nullable=False, index=True)
    public_preview_token = Column(String(128), unique=True, nullable=False, index=True)
    published_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    published_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    final_content_snapshot = Column(Text, nullable=False)
    public_access_enabled = Column(Boolean, default=True, nullable=False)

    submission = relationship("ContentSubmission", back_populates="published_content")
    publisher = relationship("User", foreign_keys=[published_by])
