import pytest
import uuid
from datetime import date, timedelta
from app.engine.evidence_engine import (
    extract_text_from_file,
    chunk_text,
    generate_embedding,
    cosine_similarity,
    extract_factual_claims,
    verify_claims_against_evidence,
    build_evidence_graph_data,
)
from app.models.organization import Organization
from app.models.knowledge_base import KnowledgeDocument, DocumentChunk, ExtractedClaim
from app.models.brand_knowledge import ApprovedFact
from app.models.submission import ContentSubmission, ContentVersion


def test_chunking_and_embedding_determinism():
    """Verify semantic chunking and embedding generation."""
    sample_text = (
        "Paragraph one introduces the AI governance system. It enforces tone and factual accuracy across all teams.\n\n"
        "Paragraph two discusses quantitative metrics. Our platform reduces regulatory compliance review cycles by 45%.\n\n"
        "Paragraph three covers security benchmarks. All documents are encrypted with AES-256 and verified against approved facts."
    )
    chunks = chunk_text(sample_text, chunk_size=150, overlap=30)
    assert len(chunks) >= 2

    # Embeddings must be deterministic unit vectors
    emb1 = generate_embedding(chunks[0])
    emb2 = generate_embedding(chunks[0])
    assert len(emb1) == 64
    assert emb1 == emb2

    # Similarity with identical text must be ~1.0
    sim = cosine_similarity(emb1, emb2)
    assert sim > 0.99


def test_claim_extraction_types():
    """Verify extraction of numerical, percentage, supremacy, and certification claims."""
    test_content = (
        "Our innovative software increases team productivity by 80%. "
        "We are the only platform in the industry that guarantees zero downtime. "
        "The system generated $10M in ARR last quarter. "
        "Our infrastructure is SOC 2 Type II certified and complies with all global privacy laws."
    )
    claims = extract_factual_claims(test_content)
    assert len(claims) >= 3

    types = [c["claim_type"] for c in claims]
    assert "performance_multiplier" in types
    assert "supremacy_claim" in types
    assert "certification" in types


def test_evidence_verification_lifecycle(db):
    """
    Test all 5 claim statuses:
    1. SUPPORTED (verified against approved fact)
    2. CONFLICTING (conflicts with official metric)
    3. OUTDATED (expired validity date)
    4. UNSUPPORTED (no source found)
    """
    org = Organization(id=str(uuid.uuid4()), name="Evidence Org", slug=f"ev-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.commit()

    # Add active approved fact: "latency reduced by 35%"
    fact_supported = ApprovedFact(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        topic="Latency Reduction",
        statement="35% latency reduction across all services",
        is_active=True,
    )
    # Add expired approved fact: "99.9% uptime"
    fact_outdated = ApprovedFact(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        topic="Cloud Uptime",
        statement="99.9% uptime guarantee for all tiers",
        expiry_date=date.today() - timedelta(days=30),  # expired
        is_active=True,
    )
    db.add_all([fact_supported, fact_outdated])
    db.commit()

    claims_to_test = [
        {
            "claim_text": "35% latency reduction",
            "sentence": "Our cloud platform delivers 35% latency reduction across all services.",
            "claim_type": "performance_multiplier",
            "severity": "high",
        },
        {
            "claim_text": "99.9% uptime guarantee",
            "sentence": "We provide a 99.9% uptime guarantee for all enterprise tiers.",
            "claim_type": "numerical_metric",
            "severity": "medium",
        },
        {
            "claim_text": "75% latency reduction",  # Conflicts with 35%
            "sentence": "Our engine achieves 75% latency reduction in production.",
            "claim_type": "performance_multiplier",
            "severity": "high",
        },
        {
            "claim_text": "increases productivity by 95%",  # Unsupported
            "sentence": "The tool increases productivity by 95% on day one.",
            "claim_type": "performance_multiplier",
            "severity": "high",
        },
    ]

    results = verify_claims_against_evidence(claims_to_test, org.id, db)
    assert len(results) == 4

    # 1. Supported
    assert results[0]["verification_status"] == "supported"
    assert "35%" in results[0]["retrieved_evidence_text"]

    # 2. Outdated
    assert results[1]["verification_status"] == "outdated"

    # 3. Conflicting
    assert results[2]["verification_status"] == "conflicting"
    assert "35%" in results[2]["explanation"]

    # 4. Unsupported
    assert results[3]["verification_status"] == "unsupported"


def test_evidence_graph_data_generation(db):
    """Verify evidence graph builder constructs valid nodes and links."""
    org = Organization(id=str(uuid.uuid4()), name="Graph Org", slug=f"gr-{uuid.uuid4().hex[:6]}")
    sub = ContentSubmission(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        title="Q4 Campaign",
        category="marketing"
    )
    claim1 = ExtractedClaim(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        organization_id=org.id,
        claim_text="SOC 2 certified",
        claim_type="certification",
        verification_status="supported",
        severity="critical",
        confidence=1.0,
        explanation="Validated against ISO registry",
        source_document_name="Security Certification 2026.pdf",
    )
    db.add_all([org, sub, claim1])
    db.commit()

    graph = build_evidence_graph_data(
        submission_id=sub.id,
        submission_title=sub.title,
        claims=[claim1],
        db=db
    )

    assert "nodes" in graph
    assert "links" in graph
    assert len(graph["nodes"]) >= 2
    assert graph["stats"]["supported_claims"] == 1
