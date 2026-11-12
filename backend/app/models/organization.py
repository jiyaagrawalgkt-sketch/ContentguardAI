import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Text
from sqlalchemy.orm import relationship
from app.core.database import Base


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    industry = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    brand_guidelines = relationship("BrandGuideline", back_populates="organization", cascade="all, delete-orphan")
    approved_facts = relationship("ApprovedFact", back_populates="organization", cascade="all, delete-orphan")
    restricted_terms = relationship("RestrictedTerm", back_populates="organization", cascade="all, delete-orphan")
    brand_assets = relationship("BrandAsset", back_populates="organization", cascade="all, delete-orphan")
    submissions = relationship("ContentSubmission", back_populates="organization", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="organization", cascade="all, delete-orphan")
    knowledge_documents = relationship("KnowledgeDocument", back_populates="organization", cascade="all, delete-orphan")
