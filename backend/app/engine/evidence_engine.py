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
    # 1. SLA, Availability & Uptime Metrics
    (
        r"\b(?:9\d(?:\.\d+)?%|100%)\s*(?:uptime|availability|sla|reliability)\b|\b(?:uptime|availability)\s*(?:of\s+)?(?:9\d(?:\.\d+)?%|100%)\b|\b(?:sub-[a-z]+|zero-downtime)\s*(?:latency|uptime|availability)\b",
        "sla_uptime",
        "high"
    ),
    # 2. Customer Support & Service Coverage
    (
        r"\b(?:24\s*/\s*7|24x7|round-the-clock)\s*(?:customer\s+support|support|monitoring|assistance|availability)?\b",
        "customer_support",
        "medium"
    ),
    # 3. Compliance, Certifications & Standards (e.g. SOC 2 Type II, ISO 27001, HIPAA)
    (
        r"\b(?:SOC\s*2(?:\s*Type\s*(?:I|II|1|2))?|ISO\s*\d{4,5}(?:-\d+)?|GDPR|HIPAA|PCI-?DSS|FedRAMP|HITRUST)\b(?:\s*(?:compliant|certified|accredited|audit))?|\b(?:certified|accredited)\s+under\s+[A-Za-z0-9\s-]+\b",
        "certification",
        "critical"
    ),
    # 4. Numerical & Percentage Multipliers (e.g. "reduces processing time by 40%", "boosts throughput by 3x")
    (
        r"\b(?:increases?|improves?|reduces?|boosts?|accelerates?|grows?|saves?)\s+[\w\s]{0,40}?\s*(?:by\s+|up\s+to\s+)?(\d+(?:\.\d+)?%|\d+(?:\.\d+)?x)(?!\w)",
        "performance_multiplier",
        "high"
    ),
    # 5. Customer Scale & Enterprise Adoption (e.g. "more than 500 enterprise customers", "spans over 50,000 active enterprises")
    (
        r"\b(?:more\s+than|over|spans?\s+over|serving|serves?|trusted\s+by)?\s*(?:\d{1,3}(?:,\d{3})+|\d+)\+?\s+(?:\w+\s+){0,2}(?:enterprise\s+customers?|enterprises?|customers?|clients?|companies?|users?|teams?|servers?|nodes?)\b",
        "scale_metric",
        "medium"
    ),
    # 6. Company History & Corporate Milestones (e.g. "established in 2018", "founded in 2020")
    (
        r"\b(?:established|founded|incorporated|started|launched)\s+in\s+\d{4}\b|\bheadquartered\s+in\s+[A-Za-z\s,]+\b",
        "company_history",
        "medium"
    ),
    # 7. Supremacy & Superlative Claims (e.g. "the only platform", "fastest platform in the industry", "industry-leading")
    (
        r"\b(?:the\s+)?(?:fastest|most\s+secure|industry-leading|number\s+one|#1|best-in-class|unrivaled|unmatched|first-ever|only\s+platform)\b(?:\s+[\w-]+){0,3}",
        "supremacy_claim",
        "high"
    ),
    # 8. Guaranteed / Zero-Risk Absolutes (e.g. "guarantees complete data protection", "zero vulnerabilities")
    (
        r"\b(?:guarantees?|guaranteed|assures?|ensures?|promises?)\s+(?:complete|total|100%|zero|unconditional|full)\s+[\w\s]{1,30}\b|\b(?:100%\s+(?:bug-free|guaranteed)|zero\s+vulnerabilities|never\s+(?:fails|crashes|downtime)|completely\s+unhackable)\b",
        "guarantee_absolute",
        "critical"
    ),
    # 9. Product Capabilities & Real-Time Features (e.g. "supports real-time threat detection")
    (
        r"\b(?:supports?|provides?|delivers?|features?|enables?)\s+(?:real-time|automated|continuous|sub-second)\s+[\w\s-]+\b",
        "product_capability",
        "high"
    ),
    # 10. Cost & Operational Metrics (e.g. "reduces operational costs", "cuts overhead")
    (
        r"\b(?:reduces?|lowers?|cuts?|eliminates?|saves?)\b(?:\s+\w+){0,3}\s+(?:operational\s+costs?|costs?|expenses?|overhead|latency|errors?|manual\s+\w+)\b",
        "cost_performance",
        "high"
    ),
    # 11. Financial & Scale Metrics (e.g. "$100M ARR", "$50M funding")
    (
        r"(?:\$|€|£)\s*\d+(?:\.\d+)?\s*(?:[KMBkmb]|million|billion|ARR|MRR)?\b",
        "financial_metric",
        "medium"
    ),
]


def extract_factual_claims(content: str) -> List[Dict[str, Any]]:
    """
    Extract factual claims, numerical metrics, supremacy statements, and compliance assertions.
    Distinguishes factual assertions from opinions, ordinary descriptions, and marketing puffery.
    Preserves exact character offsets and surrounding context.
    """
    if not content or not content.strip():
        return []

    claims = []
    sentences = re.split(r"(?<=[.!?])\s+", content.strip())

    for sentence in sentences:
        s_clean = sentence.strip()
        if not s_clean or len(s_clean) < 6:
            continue

        for pattern, claim_type, default_severity in CLAIM_PATTERNS:
            match = re.search(pattern, s_clean, re.IGNORECASE)
            if match:
                matched_str = match.group(0).strip()
                # Clean trailing punctuation from matched string
                matched_str = re.sub(r"[.,;!?]+$", "", matched_str).strip()

                # One primary factual claim assertion per sentence
                if any(c["sentence"] == s_clean for c in claims):
                    continue

                claims.append({
                    "claim_text": matched_str,
                    "sentence": s_clean,
                    "claim_type": claim_type,
                    "severity": default_severity,
                })
                break

    return claims


# --- 6. Evidence Verification Engine ---

def verify_claims_against_evidence(
    claims: List[Dict[str, Any]],
    organization_id: str,
    db: Session
) -> List[Dict[str, Any]]:
    """
    Verifies extracted claims against:
    1. Organization's ApprovedFacts Vault
    2. Knowledge Base Documents and Chunks (via isolated RAG)

    Assigns one of 5 strict statuses:
    - SUPPORTED: Corroborated by verified organizational fact or document
    - UNSUPPORTED: No approved documentation found in the knowledge base
    - CONFLICTING: Contradicts official approved figures or policies
    - OUTDATED: Supporting evidence has passed its official validity/expiry date
    - UNVERIFIED: Pending formal verification

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
        claim_lower = claim_text.lower()
        stmt_lower = sentence.lower()

        for fact in approved_facts:
            topic_lower = fact.topic.lower()
            fact_stmt_lower = (fact.statement or "").lower()

            # 1. Exact topic or number match
            if fact.verified_numbers and isinstance(fact.verified_numbers, dict):
                num_matched = False
                for k, v in fact.verified_numbers.items():
                    v_str = str(v).strip()
                    if not v_str:
                        continue
                    # Match exact numerical/token boundary rather than character substring
                    if re.search(rf"\b{re.escape(v_str)}(?!\d)", stmt_lower) or re.search(rf"\b{re.escape(v_str)}(?!\d)", claim_lower):
                        num_matched = True
                        break
                if num_matched:
                    fact_match = fact
                    break

            # 2. Direct substring overlap
            if claim_lower in fact_stmt_lower or fact_stmt_lower in stmt_lower:
                fact_match = fact
                break

            # 3. Topic words overlap
            t_words = [w for w in re.findall(r"\w{3,}", topic_lower) if w not in ["and", "for", "the", "cloud"]]
            if t_words and all(w in stmt_lower for w in t_words):
                fact_match = fact
                break

            # 4. Domain group matching (SLA/uptime/availability, latency/reduction, support/24/7)
            domain_groups = [
                {"uptime", "availability", "sla"},
                {"latency", "throughput", "speed", "reduction"},
                {"support", "assistance", "customer support", "24/7"},
                {"soc", "iso", "compliance", "cert", "certification"},
                {"customer base", "clients", "customer scale"},
                {"history", "founded", "established"},
                {"capacity", "processing"},
                {"format", "pdf", "docx"}
            ]
            domain_matched = False
            for grp in domain_groups:
                if any(w in topic_lower for w in grp) and any(w in stmt_lower or w in claim_lower for w in grp):
                    fact_match = fact
                    domain_matched = True
                    break
            if domain_matched:
                break

        if fact_match:
            source_doc_id = None  # FK is to knowledge_documents; ApprovedFact is cited by name/reference
            source_doc_name = fact_match.reference_url_or_doc or f"Approved Fact Vault: {fact_match.topic}"
            source_passage = fact_match.statement
            source_validity_date = fact_match.expiry_date

            # Check expiration
            if fact_match.expiry_date and fact_match.expiry_date < today:
                best_status = ClaimVerificationStatus.OUTDATED.value
                retrieved_evidence = f"Topic: {fact_match.topic}. Statement: {fact_match.statement}"
                explanation = f"Supporting fact for '{fact_match.topic}' expired on {fact_match.expiry_date.isoformat()}."
                suggested_correction = "Renew approval or update claim to reflect current validated data."
                recommended_action = "Update_Source"
            else:
                # Determine if claim supports or conflicts
                is_conflicting = False
                # If numbers are present, compare metrics
                claim_nums = re.findall(r"\d+(?:\.\d+)?", claim_text)
                fact_nums = re.findall(r"\d+(?:\.\d+)?", fact_match.statement)

                if claim_nums and fact_nums:
                    # If the claim states a specific number, does it match the fact's number?
                    if claim_nums[0] != fact_nums[0]:
                        is_conflicting = True

                if is_conflicting:
                    best_status = ClaimVerificationStatus.CONFLICTING.value
                    retrieved_evidence = f"Approved Fact [{fact_match.topic}]: {fact_match.statement}"
                    explanation = f"Claim statement asserts '{claim_text}', but official approved fact states '{fact_match.statement}'."
                    suggested_correction = f"Change statement to align with approved fact: '{fact_match.statement}'."
                    recommended_action = "Replace"
                else:
                    best_status = ClaimVerificationStatus.SUPPORTED.value
                    retrieved_evidence = f"Approved Fact [{fact_match.topic}]: {fact_match.statement}"
                    explanation = f"Corroborated by organization approved fact [{fact_match.topic}]: '{fact_match.statement}'."
                    recommended_action = "Approve"

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
                    explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}' in the Knowledge Base."
                    suggested_correction = f"Provide verified research citation or remove unverified claim '{claim_text}'."
                    recommended_action = "Remove"
            else:
                best_status = ClaimVerificationStatus.UNSUPPORTED.value
                explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}' in the Knowledge Base."
                suggested_correction = f"Provide verified proof or harmonize claim with official brand facts."
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
    containing Nodes and Links suitable for React Flow or SVG topology visualization.
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
                "source_document_name": claim.source_document_name,
                "source_passage": claim.source_passage,
                "source_validity_date": claim.source_validity_date.isoformat() if claim.source_validity_date else None,
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

        # Link Claim -> Source Document / Fact Vault (if source available)
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
            "total_claims": len(claims),
            "supported_claims": sum(1 for c in claims if c.verification_status == "supported"),
            "unsupported_claims": sum(1 for c in claims if c.verification_status == "unsupported"),
            "conflicting_claims": sum(1 for c in claims if c.verification_status == "conflicting"),
            "outdated_claims": sum(1 for c in claims if c.verification_status == "outdated"),
        }
    }
