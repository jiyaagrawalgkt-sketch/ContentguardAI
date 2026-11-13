import pytest
import uuid
import os
from datetime import date, timedelta
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.brand_knowledge import ApprovedFact
from app.models.multimodal import VisualAnalysisReport
from app.models.knowledge_base import ExtractedClaim
from app.engine.evidence_engine import (
    extract_factual_claims,
    verify_claims_against_evidence,
    build_evidence_graph_data,
)
from app.api.v1.endpoints.analysis import run_analysis
from scripts.seed_demo import seed_demo_environment


def test_scenario_a_all_claims_supported(db):
    """
    Scenario A: All claims supported.
    - 99.9% uptime
    - 24/7 customer support
    - SOC 2 Type II certification
    Expected:
    - 3 extracted claims
    - 3 Supported results
    - All 3 claims visible with citations in Evidence Graph
    """
    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()
    assert creator is not None

    content = "Our platform provides 99.9% uptime. We provide 24/7 customer support. Our platform is certified under SOC 2 Type II."
    raw_claims = extract_factual_claims(content)
    assert len(raw_claims) == 3, f"Expected 3 extracted claims, got {len(raw_claims)}"

    verified = verify_claims_against_evidence(raw_claims, creator.organization_id, db)
    assert len(verified) == 3

    for c in verified:
        assert c["verification_status"] == "supported", f"Claim '{c['claim_text']}' was not supported: {c['explanation']}"
        assert c["source_document_name"] is not None
        assert c["source_passage"] is not None

    # Verify Evidence Graph structure
    claim_objs = [
        ExtractedClaim(
            id=str(uuid.uuid4()),
            submission_id="sub-scenario-a",
            organization_id=creator.organization_id,
            claim_text=c["claim_text"],
            claim_type=c["claim_type"],
            verification_status=c["verification_status"],
            severity=c["severity"],
            confidence=c["confidence"],
            explanation=c["explanation"],
            source_document_name=c["source_document_name"],
            source_passage=c["source_passage"],
        )
        for c in verified
    ]
    graph = build_evidence_graph_data("sub-scenario-a", "Scenario A Title", claim_objs, db)
    assert graph["stats"]["supported_claims"] == 3
    assert graph["stats"]["unsupported_claims"] == 0
    assert len(graph["nodes"]) >= 4  # Root + 3 claims + source docs


def test_scenario_b_all_claims_unsupported(db):
    """
    Scenario B: All claims unsupported.
    3 factual claims with no approved evidence in knowledge base.
    """
    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()

    content = "Our software guarantees 100% bug-free execution. We serve more than 95,000 Martian companies. Our engine delivers sub-picosecond latency."
    raw_claims = extract_factual_claims(content)
    assert len(raw_claims) >= 2

    verified = verify_claims_against_evidence(raw_claims, creator.organization_id, db)
    for c in verified:
        assert c["verification_status"] == "unsupported"
        assert "No approved" in c["explanation"]


def test_scenario_c_mixed_claims(db):
    """
    Scenario C: Mixed claims.
    1 supported, 1 unsupported, 1 conflicting, 1 outdated.
    """
    org = Organization(id=str(uuid.uuid4()), name="Mixed Org", slug=f"mix-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.commit()

    # Supported fact: 99.9% uptime
    f1 = ApprovedFact(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        topic="SLA & Availability",
        statement="ContentGuard AI provides 99.9% uptime SLA for all tiers.",
        verified_numbers={"uptime": 99.9},
        reference_url_or_doc="SLA Agreement v1",
        is_active=True,
    )
    # Outdated fact: past expiration date
    f2 = ApprovedFact(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        topic="Latency Benchmark",
        statement="Reduces latency by 50% across microservices.",
        expiry_date=date.today() - timedelta(days=45),  # expired
        is_active=True,
    )
    db.add_all([f1, f2])
    db.commit()

    claims = [
        {"claim_text": "99.9% uptime", "sentence": "Our platform provides 99.9% uptime.", "claim_type": "sla_uptime", "severity": "high"},
        {"claim_text": "99.999% uptime", "sentence": "Our platform provides 99.999% uptime.", "claim_type": "sla_uptime", "severity": "high"},  # Conflicting with 99.9%
        {"claim_text": "reduces latency by 50%", "sentence": "Our software reduces latency by 50% on benchmarks.", "claim_type": "performance_multiplier", "severity": "high"},  # Outdated
        {"claim_text": "more than 400,000 enterprise customers", "sentence": "We serve more than 400,000 enterprise customers globally.", "claim_type": "scale_metric", "severity": "medium"},  # Unsupported
    ]

    verified = verify_claims_against_evidence(claims, org.id, db)
    statuses = {c["verification_status"] for c in verified}
    assert "supported" in statuses
    assert "conflicting" in statuses
    assert "outdated" in statuses
    assert "unsupported" in statuses


def test_scenario_d_ordinary_factual_sentences_without_numbers(db):
    """
    Scenario D: Ordinary factual sentences without numbers/percentages.
    Must extract company history, capabilities, guarantees, and operational statements.
    """
    sentences = [
        "The company was established in 2018.",
        "Our AI platform supports real-time threat detection.",
        "Our product guarantees complete data protection.",
        "Our technology reduces operational costs.",
        "Our solution is the fastest platform in the industry."
    ]
    for s in sentences:
        claims = extract_factual_claims(s)
        assert len(claims) > 0, f"Expected claim extracted from '{s}', got 0"


def test_scenario_e_zero_claims_promotional_copy(db):
    """
    Scenario E: Genuine zero factual claims (creative / promotional copy).
    Extraction completes cleanly and returns empty list with no error.
    """
    promo_copy = "We love crafting thoughtful software for human beings. Design is not just what it looks like, it is how it feels. Together we create unforgettable stories."
    claims = extract_factual_claims(promo_copy)
    assert len(claims) == 0, f"Expected 0 claims from non-factual copy, got {len(claims)}"


def test_demo_account_names(db):
    """
    Additional Requirement: Demo account names must match:
    - Administrator: Namo Tripathi
    - Reviewer: Jiya Agrawal
    - Creator: Demo Creator
    """
    seed_demo_environment(db=db)
    admin = db.query(User).filter(User.email == "admin@contentguard.demo").first()
    reviewer = db.query(User).filter(User.email == "reviewer@contentguard.demo").first()
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()

    assert admin.full_name == "Namo Tripathi", f"Expected 'Namo Tripathi', got {admin.full_name}"
    assert reviewer.full_name == "Jiya Agrawal", f"Expected 'Jiya Agrawal', got {reviewer.full_name}"
    assert creator.full_name == "Demo Creator", f"Expected 'Demo Creator', got {creator.full_name}"
