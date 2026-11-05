import pytest
from app.models.organization import Organization
from app.models.user import User
from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm
from app.engine.deterministic import run_deterministic_analysis
from app.engine.scoring import calculate_compliance_score
from app.api.v1.endpoints.brand_knowledge import get_brand_knowledge_summary
from app.core.security import hash_password


def test_varied_content_types_analysis(db):
    """
    Validates that the compliance engine dynamically detects issues across
    different marketing and business content formats without relying on hardcoded text.
    """
    # 1. Setup Organization
    org = Organization(id="org-multi-test", name="OmniCorp Global", slug="omnicorp")
    db.add(org)

    # 2. Add Brand Guidelines & Facts
    guideline = BrandGuideline(
        id="g-1",
        organization_id=org.id,
        category="policy",
        title="Zero Absolute Guarantees",
        description="Never guarantee commercial outcomes.",
        rules=["No risk-free guarantees"],
        severity_level="critical"
    )
    fact = ApprovedFact(
        id="f-1",
        organization_id=org.id,
        topic="SLA",
        statement="OmniCorp provides a 99.9% uptime SLA.",
        verified_numbers={"uptime_sla": 99.9, "evals_per_min": 12000}
    )
    term = RestrictedTerm(
        id="rt-1",
        organization_id=org.id,
        term="guaranteed 100% success",
        category="prohibited",
        severity="critical",
        suggested_alternative="proven track record of high achievement",
        reason="Absolute guarantee violates promotional policy."
    )
    db.add_all([guideline, fact, term])
    db.commit()

    # --- Scenario A: Paid Search Ad Copy (Violations) ---
    ad_copy = "Get our platform today! We offer a 100% risk-free guarantee and guaranteed growth for all clients!"
    findings_ad = run_deterministic_analysis(
        content=ad_copy,
        organization_id=org.id,
        db=db,
        category="advertisement"
    )
    assert len(findings_ad) >= 2
    types_found = [f["issue_type"] for f in findings_ad]
    assert any("Prohibited Absolute Guarantee" in t for t in types_found)
    assert any("Unqualified Commercial Guarantee" in t for t in types_found)

    score_ad, rating_ad, counts_ad = calculate_compliance_score(findings_ad)
    assert score_ad < 70
    assert counts_ad["critical"] >= 1

    # --- Scenario B: Landing Page Copy (Uptime SLA discrepancy) ---
    landing_copy = "OmniCorp Cloud infrastructure guarantees zero downtime with unbreakable security."
    findings_landing = run_deterministic_analysis(
        content=landing_copy,
        organization_id=org.id,
        db=db,
        category="landing_page"
    )
    assert len(findings_landing) >= 2
    landing_types = [f["issue_type"] for f in findings_landing]
    assert any("Factual Inconsistency" in t for t in landing_types)
    assert any("Absolute Security Claim" in t for t in landing_types)

    # --- Scenario C: Press Release (Casual tone check) ---
    press_release_informal = "Hey guys, we are announcing our revolutionary breakthrough today."
    findings_pr = run_deterministic_analysis(
        content=press_release_informal,
        organization_id=org.id,
        db=db,
        category="press_release"
    )
    assert any("Format Standard" in f["issue_type"] or "Buzzword" in f["issue_type"] for f in findings_pr)

    # --- Scenario D: Compliant Clean Content (Score >= 95) ---
    clean_copy = "OmniCorp provides enterprise cloud solutions backed by an official 99.9% uptime SLA and SOC-2 Type II certified secure architecture."
    findings_clean = run_deterministic_analysis(
        content=clean_copy,
        organization_id=org.id,
        db=db,
        category="blog_post"
    )
    assert len(findings_clean) == 0
    clean_score, clean_rating, _ = calculate_compliance_score(findings_clean)
    assert clean_score == 100.0
    assert clean_rating == "compliant"


def test_multi_tenant_data_isolation(db):
    """
    Verifies that rules and restricted terms of Organization A are strictly
    isolated and never leak to Organization B.
    """
    org_a = Organization(id="org-alpha", name="Alpha Corp", slug="alpha")
    org_b = Organization(id="org-beta", name="Beta Corp", slug="beta")
    db.add_all([org_a, org_b])

    term_a = RestrictedTerm(
        id="term-a-unique",
        organization_id=org_a.id,
        term="secret-alpha-codename",
        category="prohibited",
        severity="critical",
        suggested_alternative="public product name",
        reason="Confidential internal codename"
    )
    db.add(term_a)
    db.commit()

    test_content = "The team is deploying secret-alpha-codename to production."

    # When analyzed for Org A -> Should detect violation
    findings_a = run_deterministic_analysis(test_content, org_a.id, db)
    assert len(findings_a) == 1
    assert findings_a[0]["matched_text"] == "secret-alpha-codename"

    # When analyzed for Org B -> Must NOT detect violation (isolated tenant)
    findings_b = run_deterministic_analysis(test_content, org_b.id, db)
    assert len(findings_b) == 0


def test_brand_knowledge_summary_endpoint(db):
    """
    Verifies the Brand Knowledge summary endpoint returns active rules for the user's organization.
    """
    org = Organization(id="org-summary-test", name="Summary Corp", slug="summary-corp")
    db.add(org)
    user = User(
        id="user-summary",
        organization_id=org.id,
        email="user@summary.corp",
        hashed_password=hash_password("Password123!"),
        full_name="Summary Tester",
        role="creator",
        is_active=True
    )
    guideline = BrandGuideline(
        id="g-sum-1",
        organization_id=org.id,
        category="writing_rules",
        title="Active Voice",
        description="Always use active voice.",
        rules=["Rule 1"],
        severity_level="medium"
    )
    db.add_all([user, guideline])
    db.commit()

    summary = get_brand_knowledge_summary(current_user=user, db=db)
    assert summary["organization_id"] == org.id
    assert len(summary["guidelines"]) == 1
    assert summary["guidelines"][0]["title"] == "Active Voice"
