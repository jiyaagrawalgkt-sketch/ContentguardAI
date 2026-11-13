import uuid
from datetime import datetime, timezone, date
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Date, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class DocumentApprovalStatus(str, enum.Enum):
    APPROVED = "approved"
    PENDING = "pending"
    ARCHIVED = "archived"


class DocumentSourceType(str, enum.Enum):
    POLICY = "policy"
    RESEARCH_REPORT = "research_report"
    PRODUCT_SPEC = "product_spec"
    COMPANY_STATS = "company_stats"
    MARKETING_STATEMENT = "marketing_statement"
    FINANCIAL_AUDIT = "financial_audit"
    OTHER = "other"


class ClaimVerificationStatus(str, enum.Enum):
    SUPPORTED = "supported"
    UNSUPPORTED = "unsupported"
    CONFLICTING = "conflicting"
    OUTDATED = "outdated"
    UNVERIFIED = "unverified"


class KnowledgeDocument(Base):
    __tablename__ = "knowledge_documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False)
    source_type = Column(String(50), default=DocumentSourceType.COMPANY_STATS.value, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=True)
    mime_type = Column(String(100), default="application/pdf", nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    approval_status = Column(String(30), default=DocumentApprovalStatus.APPROVED.value, nullable=False, index=True)
    effective_date = Column(Date, default=date.today, nullable=True)
    validity_date = Column(Date, nullable=True)  # Date after which claims become OUTDATED
    review_date = Column(Date, nullable=True)
    extracted_text = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)
    created_by = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="knowledge_documents")
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    embedding_json = Column(JSON, nullable=True)  # Stored embedding vector for RAG similarity
    token_count = Column(Integer, default=0, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")


class ExtractedClaim(Base):
    __tablename__ = "extracted_claims"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    submission_id = Column(String(36), ForeignKey("content_submissions.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id = Column(String(36), ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=True, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    
    claim_text = Column(Text, nullable=False)
    sentence = Column(Text, nullable=True)  # Original sentence context
    claim_type = Column(String(50), nullable=False)  # numerical_metric, performance_multiplier, supremacy_claim, certification, absolute_statement
    claim_category = Column(String(50), nullable=True)  # Mapped assertion category
    analysis_version = Column(Integer, default=1, nullable=True)
    verification_status = Column(String(30), default=ClaimVerificationStatus.UNVERIFIED.value, nullable=False, index=True)
    severity = Column(String(20), default="high", nullable=False)
    confidence = Column(Float, default=1.0, nullable=False)
    explanation = Column(Text, nullable=False)
    
    # Evidence linkages
    retrieved_evidence_text = Column(Text, nullable=True)
    source_document_id = Column(String(36), ForeignKey("knowledge_documents.id", ondelete="SET NULL"), nullable=True)
    source_document_name = Column(String(255), nullable=True)
    source_passage = Column(Text, nullable=True)
    source_validity_date = Column(Date, nullable=True)
    
    recommended_action = Column(String(30), default="Verify", nullable=True)  # Verify, Replace, Remove, Update_Source
    suggested_correction = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    analyzed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=True)

    submission = relationship("ContentSubmission", back_populates="extracted_claims")
    source_document = relationship("KnowledgeDocument")
