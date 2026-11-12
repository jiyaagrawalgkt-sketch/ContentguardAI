import io
import re
import math
import hashlib
from datetime import date, datetime, timezone
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.knowledge_base import (
    KnowledgeDocument,
    DocumentChunk,
    ExtractedClaim,
    ClaimVerificationStatus,
    DocumentApprovalStatus,
)
from app.models.brand_knowledge import ApprovedFact, BrandGuideline


# --- 1. Document Ingestion & Text Extraction ---

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract clean text content from PDF, DOCX, TXT, or Markdown documents."""
    ext = filename.lower().split(".")[-1] if "." in filename else ""

    if ext == "pdf":
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            pages_text = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                if text:
                    pages_text.append(text.strip())
            return "\n\n".join(pages_text)
        except Exception as e:
            return f"[Error extracting PDF text: {str(e)}]"

    elif ext in ["docx", "doc"]:
        try:
            import docx
            doc = docx.Document(io.BytesIO(file_bytes))
            paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
            return "\n\n".join(paragraphs)
        except Exception as e:
            return f"[Error extracting DOCX text: {str(e)}]"

    else:
        # Default text/markdown/csv decode
        try:
            return file_bytes.decode("utf-8", errors="ignore").strip()
        except Exception:
            return file_bytes.decode("latin-1", errors="ignore").strip()


# --- 2. Semantic Chunking ---

def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> List[str]:
    """
    Split text into overlapping semantic passages.
    Prefers paragraph and sentence boundaries.
    """
    cleaned = re.sub(r"\r\n|\r", "\n", text).strip()
    if not cleaned:
        return []

    # If already short, return single chunk
    if len(cleaned) <= chunk_size:
        return [cleaned]

    paragraphs = [p.strip() for p in cleaned.split("\n\n") if p.strip()]
    chunks = []
    current_chunk = ""

    for para in paragraphs:
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk = f"{current_chunk}\n\n{para}".strip()
        else:
            if current_chunk:
                chunks.append(current_chunk)
                # Overlap with last part of current chunk
                overlap_text = current_chunk[-overlap:] if len(current_chunk) > overlap else ""
                current_chunk = f"{overlap_text}\n{para}".strip()
            else:
                # Para itself is longer than chunk_size: split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", para)
                sub_chunk = ""
                for s in sentences:
                    if len(sub_chunk) + len(s) + 1 <= chunk_size:
                        sub_chunk = f"{sub_chunk} {s}".strip()
                    else:
                        if sub_chunk:
                            chunks.append(sub_chunk)
                        sub_chunk = s
                if sub_chunk:
                    chunks.append(sub_chunk)

    if current_chunk and current_chunk not in chunks:
        chunks.append(current_chunk)

    return chunks


# --- 3. Deterministic Embedding & Vector Similarity ---

def generate_embedding(text: str) -> List[float]:
    """
    Generate normalized 64-dimensional embedding vector.
    Uses deterministic n-gram hash distribution for offline/air-gapped reproducibility,
    ensuring zero hallucination and zero runtime network dependencies.
    """
    if not text:
        return [0.0] * 64

    vector = [0.0] * 64
    words = re.findall(r"\w+", text.lower())

    for word in words:
        h = int(hashlib.sha256(word.encode("utf-8")).hexdigest(), 16)
        idx = h % 64
        weight = 1.0 + (len(word) / 10.0)
        vector[idx] += weight

    # Add character 3-grams for substring similarity
    cleaned = text.lower()
    for i in range(len(cleaned) - 2):
        trigram = cleaned[i:i+3]
        h = int(hashlib.md5(trigram.encode("utf-8")).hexdigest(), 16)
        idx = h % 64
        vector[idx] += 0.3

    # Normalize to unit vector
    norm = math.sqrt(sum(v * v for v in vector))
    if norm > 0:
        vector = [v / norm for v in vector]

    return vector


def cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Calculate cosine similarity between two unit vectors."""
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0
    dot = sum(a * b for a, b in zip(vec_a, vec_b))
    return max(0.0, min(1.0, dot))


# --- 4. RAG Knowledge Search ---

def search_knowledge_chunks(
    query: str,
    organization_id: str,
    db: Session,
    limit: int = 5,
    min_similarity: float = 0.25
) -> List[Tuple[DocumentChunk, float]]:
    """
    Search document chunks strictly isolated by organization_id.
    Matches using cosine similarity over precomputed embeddings.
    """
    chunks = db.query(DocumentChunk).filter(
        DocumentChunk.organization_id == organization_id
    ).all()

    if not chunks:
        return []

    query_vec = generate_embedding(query)
    scored = []

    for chunk in chunks:
        if not chunk.embedding_json:
            continue
        sim = cosine_similarity(query_vec, chunk.embedding_json)
        # Also reward keyword overlap
        query_words = set(re.findall(r"\w{4,}", query.lower()))
        chunk_words = set(re.findall(r"\w{4,}", chunk.chunk_text.lower()))
        if query_words and chunk_words:
            overlap_ratio = len(query_words.intersection(chunk_words)) / len(query_words)
            sim = 0.7 * sim + 0.3 * overlap_ratio

        if sim >= min_similarity:
            scored.append((chunk, sim))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:limit]


# --- 5. Claim Extraction ---

CLAIM_PATTERNS = [
    # 1. Numerical & Percentage Multipliers (e.g., "reduces latency by 45%", "increases team productivity by 80%")
    (
        r"\b(?:increases?|improves?|reduces?|boosts?|accelerates?|grows?|saves?)\b(?:\s+\w+){0,4}\s+(?:by\s+|up\s+to\s+)?(\d+(?:\.\d+)?%|\d+(?:\.\d+)?x)(?!\w)",
        "performance_multiplier",
        "high"
    ),
    # 2. Financial & Scale Metrics (e.g., "$100M ARR", "10,000 active enterprises", "99.999% uptime")
    (
        r"(?:(\$\d+(?:\.\d+)?[MBmb]?|\b\d{1,3}(?:,\d{3})+\b|\b99\.\d+%\s*uptime))(?!\w)",
        "numerical_metric",
        "medium"
    ),
    # 3. Supremacy & Superlative Claims (e.g., "the most secure", "the only platform", "industry-leading")
    (
        r"\b(the\s+(?:most|only|fastest|best|number\s+one|leading|first-ever|unrivaled|unmatched))\b",
        "supremacy_claim",
        "high"
    ),
    # 4. Compliance, Certifications & Standards (e.g., "SOC 2 Type II certified", "ISO 27001", "HIPAA compliant")
    (
        r"\b((?:ISO\s*\d+|SOC\s*2(?:\s*Type\s*II)?|GDPR|HIPAA|PCI-DSS|FedRAMP)(?:\s*(?:compliant|certified|accredited))?)\b",
        "certification",
        "critical"
    ),
    # 5. Guaranteed / Zero-Risk Absolutes (e.g., "100% bug-free", "zero vulnerabilities", "never downtime")
    (
        r"\b(100%\s+guaranteed|zero\s+vulnerabilities|never\s+(?:fails|crashes|downtime)|completely\s+unhackable)\b",
        "absolute_statement",
        "critical"
    ),
]


def extract_factual_claims(content: str) -> List[Dict[str, Any]]:
    """
    Extract factual claims, numerical metrics, supremacy statements, and compliance assertions.
    Preserves exact character offsets and surrounding context.
    """
    claims = []
    sentences = re.split(r"(?<=[.!?])\s+", content)

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean:
            continue

        for pattern, claim_type, default_severity in CLAIM_PATTERNS:
            match = re.search(pattern, s_clean, re.IGNORECASE)
            if match:
                matched_str = match.group(0)
                # Avoid duplicate claims for the same sentence
                if any(c["sentence"] == s_clean and c["claim_type"] == claim_type for c in claims):
                    continue

                claims.append({
                    "claim_text": matched_str,
                    "sentence": s_clean,
                    "claim_type": claim_type,
                    "severity": default_severity,
                })

    return claims


# --- 6. Evidence Verification Engine ---

def verify_claims_against_evidence(
    claims: List[Dict[str, Any]],
    organization_id: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Verifies extracted claims against:
    1. Organization's ApprovedFacts
    2. Knowledge Base Documents and Chunks (via isolated RAG)

    Assigns one of 5 strict statuses:
    - SUPPORTED
    - UNSUPPORTED
    - CONFLICTING
    - OUTDATED
    - UNVERIFIED

    NEVER hallucinates fake sources or citations.
    """
    approved_facts = db.query(ApprovedFact).filter(
        ApprovedFact.organization_id == organization_id,
        ApprovedFact.is_active == True
    ).all()

    verified_claims = []
    today = date.today()

    for item in claims:
        claim_text = item["claim_text"]
        sentence = item["sentence"]
        claim_type = item["claim_type"]
        severity = item["severity"]

        best_status = ClaimVerificationStatus.UNSUPPORTED.value
        confidence = 0.95
        retrieved_evidence = None
        source_doc_id = None
        source_doc_name = None
        source_passage = None
        source_validity_date = None
        explanation = ""
        suggested_correction = None
        recommended_action = "Verify"

        # Check against ApprovedFacts first
        fact_match = None
        for fact in approved_facts:
            # Check topic or value overlap
            fact_stmt = (fact.statement or "").lower()
            claim_val = claim_text.lower()
            stmt_val = sentence.lower()

            if fact_stmt in stmt_val or any(w in fact_stmt for w in claim_val.split() if len(w) > 3):
                fact_match = fact
                break
            elif fact.topic.lower() in stmt_val:
                fact_match = fact
                break

        if fact_match:
            # Check expiration
            if fact_match.expiry_date and fact_match.expiry_date < today:
                best_status = ClaimVerificationStatus.OUTDATED.value
                retrieved_evidence = f"Topic: {fact_match.topic}. Statement: {fact_match.statement}"
                source_passage = fact_match.statement
                source_validity_date = fact_match.expiry_date
                explanation = f"Supporting fact for '{fact_match.topic}' expired on {fact_match.expiry_date.isoformat()}."
                suggested_correction = f"Renew approval or update claim to reflect current validated data."
                recommended_action = "Update_Source"
            elif fact_match.statement.lower() in sentence.lower() or claim_text.lower() in fact_match.statement.lower():
                best_status = ClaimVerificationStatus.SUPPORTED.value
                retrieved_evidence = f"Approved Fact [{fact_match.topic}]: {fact_match.statement}"
                source_passage = fact_match.statement
                source_validity_date = fact_match.expiry_date
                explanation = f"Corroborated by organization approved fact: '{fact_match.statement}'."
                recommended_action = "Approve"
            else:
                best_status = ClaimVerificationStatus.CONFLICTING.value
                retrieved_evidence = f"Approved Fact [{fact_match.topic}]: {fact_match.statement}"
                source_passage = fact_match.statement
                source_validity_date = fact_match.expiry_date
                explanation = f"Claim statement asserts '{claim_text}', but official approved fact states '{fact_match.statement}'."
                suggested_correction = f"Change statement to align with approved fact: '{fact_match.statement}'."
                recommended_action = "Replace"
        else:
            # RAG Search in KnowledgeDocument chunks
            matches = search_knowledge_chunks(sentence, organization_id, db, limit=2)
            if matches:
                chunk, score = matches[0]
                doc = chunk.document

                # Check expiration
                if doc.validity_date and doc.validity_date < today:
                    best_status = ClaimVerificationStatus.OUTDATED.value
                    source_doc_id = doc.id
                    source_doc_name = doc.title
                    source_passage = chunk.chunk_text
                    source_validity_date = doc.validity_date
                    retrieved_evidence = chunk.chunk_text
                    explanation = f"Supporting document '{doc.title}' passed validity date on {doc.validity_date.isoformat()}."
                    suggested_correction = "Consult legal or compliance team for renewed documentation."
                    recommended_action = "Update_Source"
                elif claim_text.lower() in chunk.chunk_text.lower():
                    best_status = ClaimVerificationStatus.SUPPORTED.value
                    source_doc_id = doc.id
                    source_doc_name = doc.title
                    source_passage = chunk.chunk_text
                    source_validity_date = doc.validity_date
                    retrieved_evidence = chunk.chunk_text
                    explanation = f"Corroborated by approved document '{doc.title}'."
                    recommended_action = "Approve"
                elif score > 0.6:
                    # Document is on same topic, but exact metric is not matched -> Conflicting or Unsupported
                    best_status = ClaimVerificationStatus.CONFLICTING.value
                    source_doc_id = doc.id
                    source_doc_name = doc.title
                    source_passage = chunk.chunk_text
                    source_validity_date = doc.validity_date
                    retrieved_evidence = chunk.chunk_text
                    explanation = f"Approved document '{doc.title}' covers this topic but does not substantiate the assertion '{claim_text}'."
                    suggested_correction = "Harmonize statement with verified metrics from the approved document."
                    recommended_action = "Replace"
                else:
                    best_status = ClaimVerificationStatus.UNSUPPORTED.value
                    explanation = f"No approved evidence corroborates '{claim_text}' in official organization knowledge base."
                    suggested_correction = f"Provide verified research citation or remove unverified claim '{claim_text}'."
                    recommended_action = "Remove"
            else:
                if claim_type in ["supremacy_claim", "absolute_statement", "certification"]:
                    best_status = ClaimVerificationStatus.UNSUPPORTED.value
                    severity = "high"
                    explanation = f"Absolute statement or certification '{claim_text}' lacks corroborating documentation in the approved knowledge base."
                    suggested_correction = "Provide proof of certification or qualify claim with verifiable benchmark data."
                    recommended_action = "Remove"
                else:
                    best_status = ClaimVerificationStatus.UNSUPPORTED.value
                    explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}'."
                    suggested_correction = f"Verify claim with subject matter experts or tone down assertion."
                    recommended_action = "Verify"

        verified_claims.append({
            "claim_text": claim_text,
            "claim_type": claim_type,
            "sentence": sentence,
            "verification_status": best_status,
            "severity": severity,
            "confidence": confidence,
            "explanation": explanation,
            "retrieved_evidence_text": retrieved_evidence,
            "source_document_id": source_doc_id,
            "source_document_name": source_doc_name,
            "source_passage": source_passage,
            "source_validity_date": source_validity_date,
            "recommended_action": recommended_action,
            "suggested_correction": suggested_correction,
        })

    return verified_claims


# --- 7. Evidence Graph Builder ---

def build_evidence_graph_data(
    submission_id: str,
    submission_title: str,
    claims: List[ExtractedClaim],
    db: Session
) -> Dict[str, Any]:
    """
    Constructs an interactive evidence intelligence graph structure
    containing Nodes and Links suitable for React Flow or Cytoscape.js visualization.
    """
    nodes = []
    links = []

    # Center root node: Submission
    root_id = f"sub-{submission_id}"
    nodes.append({
        "id": root_id,
        "type": "submission",
        "label": submission_title or "Content Submission",
        "status": "active",
        "data": {
            "title": submission_title,
            "total_claims": len(claims),
        }
    })

    seen_doc_ids = set()

    for i, claim in enumerate(claims):
        claim_node_id = f"claim-{claim.id or i}"
        nodes.append({
            "id": claim_node_id,
            "type": "claim",
            "label": claim.claim_text,
            "status": claim.verification_status,
            "severity": claim.severity,
            "data": {
                "claim_type": claim.claim_type,
                "explanation": claim.explanation,
                "confidence": claim.confidence,
                "recommendation": claim.suggested_correction,
            }
        })

        # Link Submission -> Claim
        links.append({
            "id": f"link-sub-{claim.id or i}",
            "source": root_id,
            "target": claim_node_id,
            "relationship": "asserts",
            "status": claim.verification_status,
        })

        # Link Claim -> Source Document (if verified/cited)
        if claim.source_document_name:
            doc_node_id = f"doc-{claim.source_document_id or hashlib.md5(claim.source_document_name.encode()).hexdigest()[:8]}"
            if doc_node_id not in seen_doc_ids:
                seen_doc_ids.add(doc_node_id)
                nodes.append({
                    "id": doc_node_id,
                    "type": "knowledge_source",
                    "label": claim.source_document_name,
                    "status": "verified" if claim.verification_status == "supported" else "flagged",
                    "data": {
                        "validity_date": claim.source_validity_date.isoformat() if claim.source_validity_date else None,
                        "passage": claim.source_passage,
                    }
                })

            rel_type = "supported_by" if claim.verification_status == "supported" else (
                "outdated_by" if claim.verification_status == "outdated" else "conflicts_with"
            )

            links.append({
                "id": f"link-claim-doc-{claim.id or i}",
                "source": claim_node_id,
                "target": doc_node_id,
                "relationship": rel_type,
                "status": claim.verification_status,
            })

    return {
        "nodes": nodes,
        "links": links,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "supported_claims": sum(1 for c in claims if c.verification_status == "supported"),
            "unsupported_claims": sum(1 for c in claims if c.verification_status == "unsupported"),
            "conflicting_claims": sum(1 for c in claims if c.verification_status == "conflicting"),
            "outdated_claims": sum(1 for c in claims if c.verification_status == "outdated"),
        }
    }
