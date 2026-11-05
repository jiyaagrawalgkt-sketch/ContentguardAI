import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base


class BrandGuideline(Base):
    __tablename__ = "brand_guidelines"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=False, index=True)  # tone_voice, writing_rules, formatting, policy, visual_identity
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    rules = Column(JSON, nullable=True)  # Array of specific do's and don'ts
    severity_level = Column(String(20), default="medium", nullable=False)  # critical, high, medium, low
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="brand_guidelines")


class ApprovedFact(Base):
    __tablename__ = "approved_facts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    topic = Column(String(100), nullable=False, index=True)  # Product Specs, Financials, Company Stats
    statement = Column(Text, nullable=False)
    verified_numbers = Column(JSON, nullable=True)  # Key-value pairs of verified figures
    reference_url_or_doc = Column(String(500), nullable=True)
    effective_date = Column(Date, default=date.today, nullable=True)
    expiry_date = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="approved_facts")


class RestrictedTerm(Base):
    __tablename__ = "restricted_terms"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    term = Column(String(255), nullable=False, index=True)
    category = Column(String(50), default="prohibited", nullable=False)  # prohibited, misleading_claim, outdated_trademark, unapproved_superlative
    severity = Column(String(20), default="high", nullable=False)  # critical, high, medium, low
    suggested_alternative = Column(String(255), nullable=False)
    reason = Column(Text, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="restricted_terms")


class BrandAsset(Base):
    __tablename__ = "brand_assets"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    asset_type = Column(String(50), nullable=False)  # logo, color_palette, typography, imagery_guide
    primary_color_hex = Column(String(7), nullable=True)  # #0B0F19
    secondary_color_hex = Column(String(7), nullable=True)
    accent_color_hex = Column(String(7), nullable=True)
    file_path = Column(String(500), nullable=True)
    rules_json = Column(JSON, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    organization = relationship("Organization", back_populates="brand_assets")
