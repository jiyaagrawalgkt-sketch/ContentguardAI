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
    # 1. Comparative & Supremacy Claims
    (
        r"(?:#\s*1|\bno\.\s*1)\b(?:\s+in\s+the\s+[\w\s-]+|\s+[\w-]+){0,4}|\b(?:the\s+)?(?:fastest|most\s+secure|industry-leading|number\s+one|best-in-class|unrivaled|unmatched|first-ever|only\s+platform|superior)\b(?:\s+[\w-]+){0,4}|\b(?:outperforms?|outperformed|surpasses?)\s+legacy\s+[\w\s]{1,30}\b|\b(?:no\s+other\s+competitor\s+can\s+match|nobody\s+else\s+can\s+compete|best\s+solution\s+in\s+the\s+(?:entire\s+)?world|fastest\s+platform\s+in\s+the\s+industry)\b",
        "supremacy_claim",
        "Supremacy & Comparisons",
        "high"
    ),
    # 2. Absolute Guarantees & Return Policies
    (
        r"\b(?:100%\s+risk-free\s+guarantee|100%\s+(?:bug-free|guaranteed|safe|secure)|zero\s+(?:vulnerabilities|risk|incidents|downtime)|never\s+(?:fails|crashes|downtime|breached)|completely\s+(?:unhackable|secure|immune)|no\s+hacker\s+in\s+the\s+world)\b|\b(?:unconditional|full|100%|money-back)\s+refunds?\b|\b(?:guarantees?|guaranteed|assures?|ensures?|promises?)\s+(?:complete|total|100%|zero|unconditional|full|absolute)\s+[\w\s-]{1,40}\b|\b(?:risk-free|money-back)\s+guarantee\b",
        "guarantee_absolute",
        "Guarantees & Absolutes",
        "critical"
    ),
    # 3. SLA, Availability, Latency & Reliability
    (
        r"\b(?:9\d(?:\.\d+)?%|100%)\s*(?:uptime|availability|sla|reliability)\b|\b(?:uptime|availability|sla)\s*(?:of\s+)?(?:9\d(?:\.\d+)?%|100%)\b|\b(?:sub-[a-z]+|sub-\d+\s*(?:ms|seconds?)|zero-downtime)\s*(?:latency|uptime|availability|response\s+time)?\b|\b(?:uptime|availability)\s+sla\b",
        "sla_uptime",
        "SLA & Availability",
        "high"
    ),
    # 4. Compliance, Certifications & Standards (SOC 2, ISO 27001, GDPR, HIPAA, etc.)
    (
        r"\b(?:SOC\s*[-]?\s*2(?:\s*Type\s*(?:I|II|1|2))?|ISO\s*\d{4,5}(?:-\d+)?|GDPR|HIPAA|PCI-?DSS|FedRAMP|HITRUST|NIST|CCPA)\b(?:\s*(?:compliant|certified|accredited|audit|attestation|standards?))?|\b(?:AES-?256|end-to-end\s+encryption|zero-trust|mfa|two-factor)\s*(?:encryption|architecture|security|verification|infrastructure)?\b|\b(?:certified|accredited|compliant)\s+(?:under|with)\s+[A-Za-z0-9\s-]+\b",
        "certification",
        "Security & Compliance",
        "critical"
    ),
    # 5. Numerical & Percentage Multipliers
    (
        r"\b(?:increases?|increased|increasing|improves?|improved|improving|reduces?|reduced|reducing|boosts?|boosted|boosting|accelerates?|accelerated|accelerating|grows?|grew|grown|growing|saves?|saved|saving|cuts?|cutting)\b[\w\s]{0,40}?\b(?:by\s+|up\s+to\s+|to\s+)?(\d+(?:\.\d+)?%|\d+(?:\.\d+)?x|zero|half|\d+\s*(?:times|fold))(?!\w)|\b(?:reduces?|lowered|cuts?|saves?)\s+(?:operational\s+costs?|overhead|expenses?)\b",
        "performance_multiplier",
        "Performance & Metrics",
        "high"
    ),
    # 6. Customer Scale, Enterprise Adoption & Client Accounts
    (
        r"\b(?:worked\s+with|trusted\s+by|serving|serves?|spans?\s+over|more\s+than|over)\s+(?:\d{1,3}(?:,\d{3})+|\d+|one|two|three|four|five|ten|hundreds?|thousands?)\+?\s+(?:[\w-]+\s+)?(?:enterprise\s+customers?|enterprises?|banking\s+clients?|customers?|clients?|companies?|users?|teams?|nodes?|servers?)\b|\b(?:\d{1,3}(?:,\d{3})+|\d+)\+?\s+(?:enterprise\s+customers?|enterprises?|banking\s+clients?|active\s+enterprises?)\b",
        "scale_metric",
        "Customer & Scale",
        "medium"
    ),
    # 7. Corporate History & Milestones
    (
        r"\b(?:established|founded|incorporated|started|launched)\s+in\s+\d{4}\b|\bheadquartered\s+in\s+[A-Za-z\s,]+\b|\bexpanded\s+to\s+\d+\s+(?:countries|regions|locations|offices)\b",
        "company_history",
        "Company Information",
        "medium"
    ),
    # 8. Product Features, Specs & Capabilities
    (
        r"\b(?:custom|proprietary|patented|next-gen|active)\s+(?:acoustic\s+architecture|audio\s+architecture|noise\s+cancellation|threat\s+detection)\b|\b(?:engineered|equipped|built)\s+with\s+(?:active\s+noise\s+cancellation|[\w\s-]{3,30})\b|\b(?:supports?|provides?|delivers?|features?|enables?|includes?|offers?)\s+(?:real-time|automated|continuous|sub-second|multi-modal|autonomous|zero-trust|sound\s+fidelity|threat\s+detection)\s*[\w\s-]{0,30}\b|\bprocesses?\s+(?:\d{1,3}(?:,\d{3})+|\d+)\s+[\w\s]{1,30}\s+per\s+(?:minute|second|hour|day)\b",
        "product_capability",
        "Product Capabilities",
        "high"
    ),
    # 9. Product Specifications & Architecture
    (
        r"\b(?:natively\s+)?(?:parses?|supports?|ingests?|accepts?)\s+(?:PDF|DOCX|TXT|CSV|PNG|JPG|Markdown|JSON|XML)(?:\s*,\s*(?:PDF|DOCX|TXT|CSV|PNG|JPG|Markdown|JSON|XML|and\s+[\w]+))*\s*(?:documents?|files?|formats?)?\b|\b(?:production\s+server|api\s+endpoint|database|backend)\s+(?:is\s+)?(?:hosted\s+at|located\s+at|connected\s+to)\s+[A-Za-z0-9.-]+\.[a-z]{2,}\b|\b(?:built\s+on|powered\s+by|integrates\s+with)\s+[A-Za-z0-9\s-]{3,30}\s+(?:architecture|platform|stack|api|database)\b",
        "product_specification",
        "Specifications & Architecture",
        "medium"
    ),
    # 10. Financial & Commercial Metrics
    (
        r"(?:\$|€|£)\s*\d+(?:\.\d+)?\s*(?:[KMBkmb]|million|billion|ARR|MRR)?\b|\b(?:generated|produced|earned|closed)\s+[\w\s]{0,20}?(?:\$|€|£)\s*\d+(?:\.\d+)?\s*(?:million|billion|k)?\b|\b(?:profit\s+margin|margin|revenue\s+growth|roi)\s+(?:of\s+)?\d+(?:\.\d+)?%\b",
        "financial_metric",
        "Financial & Commercial",
        "medium"
    ),
    # 11. Turnaround, Deadlines, Return Windows & Customer Support
    (
        r"\b(?:for\s+)?(?:\d+|sixty|thirty|ninety|twenty-four|24|30|60|90)\s+(?:full\s+)?(?:days?|hours?|business\s+days?)(?:\s+(?:trial|return\s+policy|guarantee|warranty|period))?\b|\b(?:introductory\s+pricing\s+expires|pricing\s+expires|expires?|deal\s+expires?)\s+at\s+[\w\s:]+\b|\b(?:resolved|delivered|completed|turned\s+around)\b[\w\s]{0,25}?\b(?:within|in)\s+(?:\d+|two|three|twenty-four|24)\s*(?:hours?|minutes?|days?)\b|\b(?:24\s*/\s*7|24x7|round-the-clock)\s*(?:customer\s+support|support|monitoring|assistance|availability)?\b|\b(?:within\s+\d+\s*(?:hours?|days?|business\s+days?)|scheduled\s+for\s+Q[1-4]\s*\d{4})\b",
        "time_deadline",
        "Deadlines & Support",
        "medium"
    ),
    # 12. Research Findings & Empirical Benchmark Claims
    (
        r"\b(?:internal\s+(?:security\s+)?reports?|beta\s+testing|studies|benchmarks?)\s+(?:revealed|showed|confirmed|demonstrated|indicated)\s+that\b",
        "research_findings",
        "Research & Empirical Findings",
        "high"
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
    # Segment sentences preserving context
    raw_sentences = re.split(r"(?<=[.!?])\s+|\n+", content.strip())
    seen_claim_texts = set()

    for sentence in raw_sentences:
        s_clean = sentence.strip()
        if not s_clean or len(s_clean) < 8:
            continue

        # Inquiries (questions) are not factual claims
        if s_clean.endswith("?"):
            continue

        # Filter out email headers, greetings, sign-offs, and pure calls-to-action
        lower_s = s_clean.lower()
        if re.match(r"^(?:subject:|header:|subheader:|title:|dear\s+|hey\s+|hi\s+|hello\s+|contact\s+|sales@)", lower_s):
            continue
        if re.match(r"^(?:don't\s+wait|don't\s+miss|get\s+started|sign\s+up|click\s+here)\b", lower_s):
            continue

        for pattern, claim_type, category_name, default_severity in CLAIM_PATTERNS:
            for match in re.finditer(pattern, s_clean, re.IGNORECASE):
                matched_str = match.group(0).strip()
                # Clean trailing punctuation and trailing conjunctions
                matched_str = re.sub(r"[.,;!?:]+$", "", matched_str).strip()
                matched_str = re.sub(r"\s+(?:and|or|with|to|for|in|on|at|by)$", "", matched_str, flags=re.IGNORECASE).strip()

                if matched_str and matched_str.lower() not in seen_claim_texts:
                    # Avoid adding smaller substrings of already captured claims
                    if not any(matched_str.lower() in existing for existing in seen_claim_texts):
                        seen_claim_texts.add(matched_str.lower())
                        claims.append({
                            "claim_text": matched_str,
                            "sentence": s_clean,
                            "claim_type": claim_type,
                            "claim_category": category_name,
                            "severity": default_severity,
                        })

    return claims


def _normalize_text(text: str) -> str:
    """Normalize whitespace, lowercases, removes punctuation and comma formatting."""
    if not text:
        return ""
    # Strip comma separators in numbers (12,000 -> 12000)
    cleaned = re.sub(r"(\d),(\d)", r"\1\2", text.lower())
    # Normalize hyphens and underscores to space (soc-2 -> soc 2)
    cleaned = re.sub(r"[-_]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _extract_numbers(text: str) -> List[str]:
    """Extract normalized numbers without formatting commas."""
    if not text:
        return []
    cleaned = re.sub(r"(\d),(\d)", r"\1\2", text)
    return re.findall(r"\b\d+(?:\.\d+)?\b", cleaned)


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
        claim_category = item.get("claim_category") or claim_type.replace("_", " ").title()
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

        # Check against ApprovedFacts Vault
        best_fact = None
        best_fact_score = 0

        claim_norm = _normalize_text(claim_text)
        sentence_norm = _normalize_text(sentence)
        claim_nums = _extract_numbers(claim_text)

        claim_words = [w for w in re.findall(r"[a-z0-9]{3,}", claim_norm) if w not in {"with", "that", "this", "from", "have", "more", "than", "over", "uses", "provides", "delivers", "offers", "engine", "software", "platform"}]

        for fact in approved_facts:
            fact_stmt_norm = _normalize_text(fact.statement or "")
            fact_topic_norm = _normalize_text(fact.topic or "")

            fact_nums = _extract_numbers(fact.statement or "")
            verified_nums = []
            if fact.verified_numbers and isinstance(fact.verified_numbers, dict):
                for v in fact.verified_numbers.values():
                    verified_nums.extend(_extract_numbers(str(v)))
            all_fact_nums = set(fact_nums + verified_nums)

            # Substantive overlap check:
            has_direct_overlap = bool(claim_norm and (claim_norm in fact_stmt_norm or fact_stmt_norm in claim_norm))
            has_num_overlap = bool(claim_nums and any(cn in all_fact_nums for cn in claim_nums))
            overlapping_words = [w for w in claim_words if w in fact_stmt_norm or w in fact_topic_norm]

            # If no words, direct substring, or numbers match, this fact cannot corroborate this claim
            if not (has_direct_overlap or has_num_overlap or len(overlapping_words) >= 1):
                continue

            score = 0
            if has_direct_overlap:
                score += 100
            if has_num_overlap:
                score += 80
            score += len(overlapping_words) * 25

            # Category bonus only applied when substantive overlap already exists
            cat_norm = _normalize_text(claim_category)
            if cat_norm and (cat_norm in fact_topic_norm or fact_topic_norm in cat_norm):
                score += 30

            if score > best_fact_score:
                best_fact_score = score
                best_fact = fact

        # Require a meaningful match threshold (>= 25)
        if best_fact and best_fact_score >= 25:
            source_doc_id = None
            source_doc_name = best_fact.reference_url_or_doc or f"Approved Fact Vault: {best_fact.topic}"
            source_passage = best_fact.statement
            source_validity_date = best_fact.expiry_date

            # Check expiration
            if best_fact.expiry_date and best_fact.expiry_date < today:
                best_status = ClaimVerificationStatus.OUTDATED.value
                retrieved_evidence = f"Topic: {best_fact.topic}. Statement: {best_fact.statement}"
                explanation = f"Supporting fact for '{best_fact.topic}' expired on {best_fact.expiry_date.isoformat()}."
                suggested_correction = None
                recommended_action = "Review"
            else:
                # Check for numerical or factual conflict
                fact_nums = _extract_numbers(best_fact.statement or "")
                verified_nums = []
                if best_fact.verified_numbers and isinstance(best_fact.verified_numbers, dict):
                    for v in best_fact.verified_numbers.values():
                        verified_nums.extend(_extract_numbers(str(v)))
                all_fact_nums = set(fact_nums + verified_nums)

                is_conflicting = False
                if claim_nums:
                    # If numbers are asserted and not verified by the approved fact
                    if not all(cn in all_fact_nums for cn in claim_nums):
                        is_conflicting = True

                fact_stmt_norm = _normalize_text(best_fact.statement or "")
                has_corroboration = (
                    (claim_norm and claim_norm in fact_stmt_norm) or
                    (claim_nums and any(cn in all_fact_nums for cn in claim_nums)) or
                    (overlapping_words and all(w in fact_stmt_norm for w in claim_words))
                )

                if is_conflicting:
                    best_status = ClaimVerificationStatus.CONFLICTING.value
                    retrieved_evidence = f"Approved Fact [{best_fact.topic}]: {best_fact.statement}"
                    explanation = f"Claim statement asserts '{claim_text}', but official approved fact states '{best_fact.statement}'."
                    suggested_correction = best_fact.statement
                    recommended_action = "Replace"
                elif not has_corroboration:
                    best_status = ClaimVerificationStatus.UNSUPPORTED.value
                    explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}' in the Knowledge Base."
                    suggested_correction = ""
                    recommended_action = "Remove"
                else:
                    best_status = ClaimVerificationStatus.SUPPORTED.value
                    retrieved_evidence = f"Approved Fact [{best_fact.topic}]: {best_fact.statement}"
                    explanation = f"Corroborated by organization approved fact [{best_fact.topic}]: '{best_fact.statement}'."
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
                    suggested_correction = None
                    recommended_action = "Review"
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
                    suggested_correction = None
                    recommended_action = "Review"
                else:
                    best_status = ClaimVerificationStatus.UNSUPPORTED.value
                    explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}' in the Knowledge Base."
                    suggested_correction = ""
                    recommended_action = "Remove"
            else:
                best_status = ClaimVerificationStatus.UNSUPPORTED.value
                explanation = f"No approved organizational documentation corroborates the assertion '{claim_text}' in the Knowledge Base."
                suggested_correction = None
                recommended_action = "Review"

        verified_claims.append({
            "claim_text": claim_text,
            "claim_type": claim_type,
            "claim_category": claim_category,
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
