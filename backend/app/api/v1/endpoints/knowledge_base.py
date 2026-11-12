import os
import uuid
from datetime import datetime, timezone, date
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.database import get_db
from app.core.permissions import get_current_user, require_admin, require_any_authenticated
from app.models.user import User
from app.models.knowledge_base import (
    KnowledgeDocument,
    DocumentChunk,
    DocumentApprovalStatus,
    DocumentSourceType,
)
from app.models.audit import AuditLog
from app.engine.evidence_engine import (
    extract_text_from_file,
    chunk_text,
    generate_embedding,
)

router = APIRouter()

UPLOAD_DIR = os.path.join(os.getcwd(), "uploads", "knowledge_base")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload", status_code=status.HTTP_201_CREATED, summary="Upload Approved Knowledge Document")
async def upload_knowledge_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    source_type: str = Form("company_stats"),
    version: str = Form("1.0"),
    validity_date: Optional[str] = Form(None),
    review_date: Optional[str] = Form(None),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """
    Ingest official organizational document (PDF, DOCX, TXT).
    Extracts text, builds semantic overlapping chunks, computes normalized embeddings,
    and indexes for Zero-Trust Evidence Intelligence retrieval.
    """
    # Validate extension
    filename = file.filename or "document.txt"
    ext = filename.lower().split(".")[-1] if "." in filename else ""
    if ext not in ["pdf", "docx", "doc", "txt", "md"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported document format. Allowed formats: PDF, DOCX, TXT, MD"
        )

    file_bytes = await file.read()
    if len(file_bytes) > 20 * 1024 * 1024:  # 20MB limit
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum 20MB limit"
        )

    # Secure file save
    safe_filename = f"{uuid.uuid4().hex[:12]}_{filename}"
    file_path = os.path.join(UPLOAD_DIR, safe_filename)
    with open(file_path, "wb") as f:
        f.write(file_bytes)

    # 1. Text Extraction
    extracted_text = extract_text_from_file(file_bytes, filename)

    # Parse dates
    parsed_validity = None
    if validity_date:
        try:
            parsed_validity = date.fromisoformat(validity_date.strip())
        except Exception:
            pass

    parsed_review = None
    if review_date:
        try:
            parsed_review = date.fromisoformat(review_date.strip())
        except Exception:
            pass

    # 2. Create KnowledgeDocument
    doc_id = str(uuid.uuid4())
    doc = KnowledgeDocument(
        id=doc_id,
        organization_id=current_user.organization_id,
        title=title.strip(),
        source_type=source_type,
        file_name=filename,
        file_path=file_path,
        mime_type=file.content_type or "application/octet-stream",
        file_size_bytes=len(file_bytes),
        version=version.strip(),
        approval_status=DocumentApprovalStatus.APPROVED.value,
        effective_date=date.today(),
        validity_date=parsed_validity,
        review_date=parsed_review,
        extracted_text=extracted_text,
        created_by=current_user.id,
    )
    db.add(doc)
    db.flush()

    # 3. Semantic Chunking & Embedding Generation
    chunks = chunk_text(extracted_text, chunk_size=400, overlap=80)
    for idx, chunk_str in enumerate(chunks):
        emb = generate_embedding(chunk_str)
        token_count = len(chunk_str.split())
        db_chunk = DocumentChunk(
            id=str(uuid.uuid4()),
            document_id=doc_id,
            organization_id=current_user.organization_id,
            chunk_index=idx,
            chunk_text=chunk_str,
            embedding_json=emb,
            token_count=token_count,
        )
        db.add(db_chunk)

    # 4. Audit Log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="KNOWLEDGE_DOC_UPLOADED",
        entity_type="knowledge_document",
        entity_id=doc_id,
        details={
            "title": title,
            "filename": filename,
            "chunks_count": len(chunks),
            "validity_date": parsed_validity.isoformat() if parsed_validity else None,
        }
    )
    db.add(audit)
    db.commit()
    db.refresh(doc)

    return {
        "id": doc.id,
        "title": doc.title,
        "source_type": doc.source_type,
        "file_name": doc.file_name,
        "chunks_indexed": len(chunks),
        "validity_date": doc.validity_date.isoformat() if doc.validity_date else None,
        "approval_status": doc.approval_status,
        "message": f"Successfully indexed '{doc.title}' into Evidence Intelligence Graph ({len(chunks)} chunks)."
    }


@router.get("/", summary="List Organization Knowledge Documents")
def list_knowledge_documents(
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """List all approved knowledge sources for current user's organization."""
    docs = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.organization_id == current_user.organization_id
    ).order_by(desc(KnowledgeDocument.created_at)).all()

    items = []
    today = date.today()
    for d in docs:
        is_expired = bool(d.validity_date and d.validity_date < today)
        items.append({
            "id": d.id,
            "title": d.title,
            "source_type": d.source_type,
            "file_name": d.file_name,
            "file_size_bytes": d.file_size_bytes,
            "version": d.version,
            "approval_status": d.approval_status,
            "effective_date": d.effective_date.isoformat() if d.effective_date else None,
            "validity_date": d.validity_date.isoformat() if d.validity_date else None,
            "is_expired": is_expired,
            "chunks_count": len(d.chunks),
            "created_at": d.created_at.isoformat(),
        })

    return items


@router.get("/{doc_id}", summary="Get Knowledge Document Details and Chunks")
def get_knowledge_document(
    doc_id: str,
    current_user: User = Depends(require_any_authenticated),
    db: Session = Depends(get_db),
):
    """Retrieve full document text and chunk preview strictly isolated by organization."""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.organization_id == current_user.organization_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return {
        "id": doc.id,
        "title": doc.title,
        "source_type": doc.source_type,
        "file_name": doc.file_name,
        "version": doc.version,
        "approval_status": doc.approval_status,
        "effective_date": doc.effective_date.isoformat() if doc.effective_date else None,
        "validity_date": doc.validity_date.isoformat() if doc.validity_date else None,
        "extracted_text_preview": (doc.extracted_text[:1200] + "...") if doc.extracted_text and len(doc.extracted_text) > 1200 else doc.extracted_text,
        "chunks": [
            {
                "id": c.id,
                "chunk_index": c.chunk_index,
                "chunk_text": c.chunk_text,
                "token_count": c.token_count,
            }
            for c in doc.chunks
        ]
    }


@router.delete("/{doc_id}", summary="Delete Knowledge Document")
def delete_knowledge_document(
    doc_id: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete knowledge document and cascade remove all indexed vector chunks."""
    doc = db.query(KnowledgeDocument).filter(
        KnowledgeDocument.id == doc_id,
        KnowledgeDocument.organization_id == current_user.organization_id
    ).first()

    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    title = doc.title
    db.delete(doc)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="KNOWLEDGE_DOC_DELETED",
        entity_type="knowledge_document",
        entity_id=doc_id,
        details={"title": title}
    )
    db.add(audit)
    db.commit()

    return {"message": f"Successfully deleted '{title}' and removed associated evidence chunks."}
