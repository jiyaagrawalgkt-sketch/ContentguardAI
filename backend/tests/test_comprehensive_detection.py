import pytest
from app.models.organization import Organization
from app.models.brand_knowledge import BrandGuideline
from app.engine.deterministic import run_deterministic_analysis, mask_sensitive_preview
from app.engine.gemini_analyzer import analyze_content, redact_secrets_for_ai
from app.models.analysis import IssueSeverity, IssueCategory


def test_user_multi_violation_sample(db):
    """
    Verifies that the exact sample from the user request detects ALL 9 distinct issues
    across categories from beginning, middle, and end of text.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    sample_text = (
        "Our solution is 100% secure and offers a completely bulletproof data solution. "
        "After testing with our confidential Tier-1 banking clients in New York, we eliminated all system latency. "
        "ContentGuard guarantees a 500% increase in productivity, making it impossible for hackers to breach your infrastructure. "
        "This replaces the need for third-party firewalls or traditional antivirus software, saving you millions of dollars instantly."
    )

    issues = run_deterministic_analysis(
        content=sample_text,
        organization_id=org_id,
        db=db
    )

    matched_texts = [i["matched_text"] for i in issues]
    categories = [i.get("category") for i in issues]

    # Verify all 9 issues are detected
    assert any("100% secure" in m for m in matched_texts), "Should detect '100% secure'"
    assert any("completely bulletproof data solution" in m for m in matched_texts), "Should detect 'completely bulletproof data solution'"
    assert any("confidential Tier-1 banking clients" in m for m in matched_texts), "Should detect 'confidential Tier-1 banking clients'"
    assert any("New York" in m for m in matched_texts), "Should detect 'New York' sensitive location"
    assert any("eliminated all system latency" in m for m in matched_texts), "Should detect 'eliminated all system latency'"
    assert any("guarantees a 500% increase" in m for m in matched_texts), "Should detect 'guarantees a 500% increase'"
    assert any("impossible for hackers to breach your infrastructure" in m for m in matched_texts), "Should detect 'impossible for hackers to breach your infrastructure'"
    assert any("replaces the need for third-party firewalls or traditional antivirus software" in m for m in matched_texts), "Should detect replacement claim"
    assert any("saving you millions of dollars instantly" in m for m in matched_texts), "Should detect 'saving you millions of dollars instantly'"

    assert len(issues) >= 9, f"Expected at least 9 issues, got {len(issues)}"

    # Check categories
    assert "confidentiality" in categories
    assert "misleading_claim" in categories


def test_pii_and_security_credentials(db):
    """
    Verifies detection of AWS keys, database connection strings, personal emails,
    phone numbers, SSNs, and credit cards.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    text = (
        "Contact direct line at +1 (555) 321-9876 or personal email sarah.connor@gmail.com. "
        "Client SSN is 000-12-3456 and CC is 4111-2222-3333-4444. "
        "AWS credentials: AKIAIOSFODNN7EXAMPLE. "
        "Connect via postgresql://admin:secret123@10.0.1.5:5432/production_db."
    )

    issues = run_deterministic_analysis(
        content=text,
        organization_id=org_id,
        db=db
    )

    matched_texts = [i["matched_text"] for i in issues]
    types = [i["issue_type"] for i in issues]

    assert any("AKIAIOSFODNN7EXAMPLE" in m for m in matched_texts)
    assert any("sarah.connor@gmail.com" in m for m in matched_texts)
    assert any("555) 321-9876" in m for m in matched_texts)
    assert any("000-12-3456" in m for m in matched_texts)
    assert any("4111-2222-3333-4444" in m for m in matched_texts)
    assert any("postgresql://admin:secret123" in m for m in matched_texts)

    # Check mask function
    masked_aws = mask_sensitive_preview("AKIAIOSFODNN7EXAMPLE", "security_technical")
    assert "AKIA" in masked_aws and "EXAMPLE" not in masked_aws

    masked_email = mask_sensitive_preview("sarah.connor@gmail.com", "privacy")
    assert "sa****@gmail.com" == masked_email


def test_credential_redaction_before_external_ai():
    """
    Verifies that passwords, API keys, and connection strings are completely redacted
    before content is passed to external AI services.
    """
    raw_content = (
        "Deploy using AWS key AKIAIOSFODNN7EXAMPLE and GitHub token ghp_1234567890abcdef1234567890abcdef1234. "
        "Database is postgresql://superadmin:TopSecretPassword99@db.internal:5432/main."
    )

    sanitized = redact_secrets_for_ai(raw_content)

    assert "AKIAIOSFODNN7EXAMPLE" not in sanitized
    assert "[REDACTED_AWS_KEY]" in sanitized

    assert "ghp_1234567890abcdef1234567890abcdef1234" not in sanitized
    assert "[REDACTED_GITHUB_TOKEN]" in sanitized

    assert "TopSecretPassword99" not in sanitized
    assert "[REDACTED_DATABASE_URI]" in sanitized


def test_duplicate_sentence_detection(db):
    """
    Verifies detection of redundant repeated sentences.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    text = (
        "Our platform provides automated brand governance for modern growth teams. "
        "We help enterprise marketing leaders ship compliant copy with total velocity. "
        "Our platform provides automated brand governance for modern growth teams."
    )

    issues = run_deterministic_analysis(
        content=text,
        organization_id=org_id,
        db=db
    )

    assert any(i.get("category") == "unnecessary_content" for i in issues)
    dup_issue = next(i for i in issues if i.get("category") == "unnecessary_content")
    assert "Redundant Duplicate Sentence" in dup_issue["issue_type"]
    assert dup_issue["recommended_action"] == "Remove"


def test_completely_compliant_content(db):
    """
    Verifies that a well-written, factual, professional corporate release generates
    zero violations and a perfect compliance score.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    compliant_text = (
        "Acme Global Technologies provides enterprise brand governance solutions. "
        "Our infrastructure operates under SOC-2 Type II standards, delivering a verified 99.9% uptime SLA. "
        "Marketing teams can review messaging against organizational guidelines prior to publication."
    )

    issues, score, rating, counts, _ = analyze_content(
        content=compliant_text,
        organization_id=org_id,
        db=db
    )

    assert len(issues) == 0
    assert score == 100.0
    assert rating == "compliant"
    assert counts["critical"] == 0
    assert counts["high"] == 0


def test_false_positive_control_public_entities(db):
    """
    Verifies that legitimate public entities, recognized cities, and verified numbers
    are NOT falsely flagged as confidential data leaks.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    public_text = (
        "Our global office in New York is located near Times Square. "
        "We serve clients worldwide across London, Tokyo, and Singapore. "
        "Over 500 enterprise customers rely on our verified 99.9% uptime SLA."
    )

    issues = run_deterministic_analysis(
        content=public_text,
        organization_id=org_id,
        db=db
    )

    # Legitimate cities without confidential client context should NOT be flagged as data leaks
    confidential_issues = [i for i in issues if i.get("category") == "confidentiality"]
    assert len(confidential_issues) == 0, f"Expected 0 confidential leaks, got {confidential_issues}"


def test_dismiss_finding_flow(db):
    """
    Verifies that creators can dismiss a finding with a formal compliance note,
    and that the finding correctly stores and returns its dismissed status.
    """
    from scripts.seed_demo import seed_demo_environment
    from app.models.user import User
    from app.schemas.submission import SubmissionCreate
    from app.api.v1.endpoints.submissions import create_submission
    from app.api.v1.endpoints.analysis import run_analysis, dismiss_issue, IssueDismissRequest

    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.role == "creator").first()

    sub = create_submission(
        payload=SubmissionCreate(
            title="Dismiss Test Draft",
            category="social_media",
            content="Our confidential Tier-1 banking clients in New York love our platform."
        ),
        current_user=creator,
        db=db
    )

    report = run_analysis(submission_id=sub.id, current_user=creator, db=db)
    assert len(report.issues) > 0

    first_issue = report.issues[0]
    dismiss_res = dismiss_issue(
        issue_id=first_issue.id,
        payload=IssueDismissRequest(reason="Authorized public client reference"),
        current_user=creator,
        db=db
    )

    assert dismiss_res["message"] == "Issue dismissed successfully"
    assert dismiss_res["dismiss_reason"] == "Authorized public client reference"

    # Re-fetch report
    from app.models.analysis import DetectedIssue
    db_issue = db.query(DetectedIssue).filter(DetectedIssue.id == first_issue.id).first()
    assert db_issue.is_dismissed is True
    assert db_issue.dismiss_reason == "Authorized public client reference"


def test_multi_violation_fix_and_reanalysis_score_improvement(db):
    """
    Verifies the complete life-cycle of submitting content with multiple violations,
    fixing every flagged phrase, and re-analyzing to verify score increases to 100.
    """
    from scripts.seed_demo import seed_demo_environment
    from app.models.user import User
    from app.schemas.submission import SubmissionCreate, SubmissionUpdateContent
    from app.api.v1.endpoints.submissions import create_submission, update_submission_content
    from app.api.v1.endpoints.analysis import run_analysis

    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.role == "creator").first()

    # Initial draft with violations
    initial_text = "We offer a 100% risk-free guarantee and our software is 100% secure."
    sub = create_submission(
        payload=SubmissionCreate(
            title="Score Improvement Test",
            category="social_media",
            content=initial_text
        ),
        current_user=creator,
        db=db
    )

    # First analysis: low score
    report1 = run_analysis(submission_id=sub.id, current_user=creator, db=db)
    assert report1.compliance_score < 70
    assert report1.total_issues >= 2

    # Fix all issues
    cleaned_text = "We offer proven satisfaction and our software is built on SOC-2 verified secure architecture."
    update_submission_content(
        id=sub.id,
        payload=SubmissionUpdateContent(content=cleaned_text, change_summary="Applied recommended fixes"),
        current_user=creator,
        db=db
    )

    # Re-analysis: high compliant score
    report2 = run_analysis(submission_id=sub.id, current_user=creator, db=db)
    assert report2.compliance_score >= 95
    assert report2.total_issues == 0


def test_deterministic_fallback_when_gemini_unavailable(db):
    """
    Verifies that when GEMINI_API_KEY is not configured, the system gracefully falls back
    to deterministic rules without crashing, identifying violations and returning fallback mode.
    """
    from app.core.config import settings
    original_key = settings.GEMINI_API_KEY
    settings.GEMINI_API_KEY = ""

    try:
        org = db.query(Organization).first()
        org_id = org.id if org else "test-org"

        issues, score, rating, counts, engine_mode = analyze_content(
            content="Our product provides a 100% risk-free guarantee for all clients.",
            organization_id=org_id,
            db=db
        )

        assert engine_mode == "deterministic_fallback"
        assert len(issues) >= 1
        assert any("100% risk-free guarantee" in i["matched_text"] for i in issues)
        assert score < 80
    finally:
        settings.GEMINI_API_KEY = original_key


def test_organization_custom_compliance_policy(db):
    """
    Verifies that organization-specific restricted terms are strictly isolated:
    Org A's custom restricted term is flagged in Org A's drafts, but NOT in Org B's drafts.
    """
    from app.models.brand_knowledge import RestrictedTerm

    org_a = Organization(id="org-policy-a", name="Alpha Corp", slug="alpha-corp")
    org_b = Organization(id="org-policy-b", name="Beta Corp", slug="beta-corp")
    db.add_all([org_a, org_b])
    db.commit()

    # Org A restricts the code name "Project-Valkyrie"
    term_a = RestrictedTerm(
        id="term-valkyrie",
        organization_id=org_a.id,
        term="Project-Valkyrie",
        category="prohibited",
        severity="critical",
        suggested_alternative="our upcoming enterprise release",
        reason="Unannounced confidential internal codename."
    )
    db.add(term_a)
    db.commit()

    test_content = "We are preparing to launch Project-Valkyrie next month."

    # Scan in Org A: must be flagged as Critical
    issues_a = run_deterministic_analysis(
        content=test_content,
        organization_id=org_a.id,
        db=db
    )
    assert any("Project-Valkyrie" in i["matched_text"] for i in issues_a)
    valk_issue = next(i for i in issues_a if "Project-Valkyrie" in i["matched_text"])
    assert valk_issue["severity"] == "critical"

    # Scan in Org B: must NOT be flagged as Org B did not restrict it
    issues_b = run_deterministic_analysis(
        content=test_content,
        organization_id=org_b.id,
        db=db
    )
    assert not any("Project-Valkyrie" in i["matched_text"] for i in issues_b)


def test_urgent_bug_fix_sample_all_violations(db):
    """
    CRITICAL REGRESSION TEST for user's reported bug:
    Verifies that all 12 distinct violations in the user's sample are detected,
    score is 0/100 (critical_violations), and never defaults to 100/100.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    test_content = (
        "ContentGuard guarantees 100% security and completely eliminates every cybersecurity risk. "
        "After testing with confidential client JPMorgan Chase, we improved operational efficiency by 500%. "
        "Our financial results show $12.8 million in revenue with an expected profit margin of 87%, which is not yet approved for public release. "
        "No hacker in the world can ever breach our infrastructure with our 99.9% uptime SLA forever. "
        "Our upcoming enterprise platform release is upcoming enterprise platform release. "
        "Connect to internal infrastructure at api.acme.com for the biggest, greatest, most powerful, most advanced, and most revolutionary product ever created."
    )

    issues, score, rating, counts, engine_mode = analyze_content(
        content=test_content,
        organization_id=org_id,
        db=db
    )

    matched_texts = [i["matched_text"] for i in issues]
    categories = [i.get("category") for i in issues]

    # Verify every required issue is detected
    assert any("guarantees 100% security" in m for m in matched_texts), "Should detect 'guarantees 100% security'"
    assert any("completely eliminates every cybersecurity risk" in m for m in matched_texts), "Should detect 'completely eliminates every cybersecurity risk'"
    assert any("JPMorgan Chase" in m for m in matched_texts), "Should detect confidential banking client 'JPMorgan Chase'"
    assert any("improved operational efficiency by 500%" in m for m in matched_texts), "Should detect 'improved operational efficiency by 500%'"
    assert any("$12.8 million in revenue" in m for m in matched_texts), "Should detect '$12.8 million in revenue'"
    assert any("expected profit margin of 87%" in m for m in matched_texts), "Should detect 'expected profit margin of 87%'"
    assert any("not yet approved for public release" in m for m in matched_texts), "Should detect 'not yet approved for public release'"
    assert any("No hacker in the world can ever breach our infrastructure" in m for m in matched_texts), "Should detect 'No hacker in the world can ever breach our infrastructure'"
    assert any("99.9% uptime SLA forever" in m for m in matched_texts), "Should detect '99.9% uptime SLA forever'"
    assert any("upcoming enterprise platform release is upcoming enterprise platform release" in m for m in matched_texts), "Should detect duplicate phrase"
    assert any("api.acme.com" in m for m in matched_texts), "Should detect internal infrastructure endpoint"
    assert any("biggest, greatest, most powerful" in m for m in matched_texts), "Should detect excessive superlatives"

    assert len(issues) >= 12, f"Expected at least 12 issues, got {len(issues)}"
    assert score == 0.0, f"Score for highly non-compliant content must be 0, got {score}"
    assert rating == "critical_violations"
    assert counts["critical"] >= 5


def test_single_issue_submission(db):
    """
    Verifies that a submission with only one minor issue returns score around 85-95
    with exact single finding.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    text = "We built our new release using our proprietary AI engine to help teams."
    issues, score, rating, counts, _ = analyze_content(
        content=text,
        organization_id=org_id,
        db=db
    )

    assert len(issues) == 1
    assert issues[0]["matched_text"] == "proprietary AI engine"
    assert score > 90.0
    assert counts["critical"] == 0


def test_first_and_last_paragraph_issues(db):
    """
    Verifies that issues occurring in the first paragraph AND last paragraph are both
    detected and sorted chronologically.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    text = (
        "This first paragraph guarantees 100% security for all users.\n\n"
        "This middle paragraph describes our verified architecture according to industry standards.\n\n"
        "This last paragraph promises that our 99.9% uptime SLA forever will satisfy you."
    )

    issues, score, rating, counts, _ = analyze_content(
        content=text,
        organization_id=org_id,
        db=db
    )

    assert len(issues) >= 2
    # First issue from first paragraph
    assert "guarantees 100% security" in issues[0]["matched_text"]
    # Last issue from last paragraph
    assert "99.9% uptime SLA forever" in issues[-1]["matched_text"]
    assert issues[0]["char_start"] < issues[-1]["char_start"]


def test_analysis_failure_handling(db):
    """
    Verifies that if submission content is unprocessable or analysis endpoint crashes,
    it raises a 500 error instead of silently returning score 100.
    """
    from fastapi import HTTPException
    from app.api.v1.endpoints.analysis import run_analysis
    from scripts.seed_demo import seed_demo_environment
    from app.models.user import User
    from app.models.submission import ContentSubmission

    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.role == "creator").first()

    # Submission with no version
    sub = ContentSubmission(
        id="empty-sub-no-version",
        organization_id=creator.organization_id,
        creator_id=creator.id,
        title="Empty Sub",
        category="social_media"
    )
    db.add(sub)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        run_analysis(submission_id="empty-sub-no-version", current_user=creator, db=db)

    assert exc_info.value.status_code == 400
    assert "no content versions" in exc_info.value.detail.lower()


def test_smartwork_promotional_detection(db):
    """
    Verifies that the SmartWork AI promotional copy accurately triggers all 6 expected categories:
    1. Unsupported productivity guarantees
    2. Exaggerated superlatives
    3. Absolute claims
    4. Repeated product messaging
    5. Duplicate or unnecessary promotional sentences
    6. Content quality and readability issues
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    smartwork_text = (
        "Introducing SmartWork AI!\n\n"
        "SmartWork AI is the best productivity platform in the world. It is the greatest and most amazing tool ever developed.\n\n"
        "Our software guarantees that every employee will become 10 times more productive within just one day.\n\n"
        "You will never need another productivity application again. Our platform solves every business problem and guarantees perfect results.\n\n"
        "SmartWork AI helps teams organize their tasks, collaborate with colleagues, and manage projects from one dashboard.\n\n"
        "SmartWork AI is amazing. SmartWork AI is revolutionary. SmartWork AI is the best. It is the most powerful platform, the greatest platform, and the only platform your business will ever need.\n\n"
        "Try SmartWork AI today and transform the way your team works!"
    )

    issues, score, rating, counts, _ = analyze_content(
        content=smartwork_text,
        organization_id=org_id,
        db=db
    )

    matched_texts = [i["matched_text"] for i in issues]
    issue_types = [i["issue_type"] for i in issues]
    categories = [i.get("category") for i in issues]

    # 1. Unsupported Productivity Guarantee
    assert any("10 times more productive" in m for m in matched_texts), "Should detect productivity multiplier guarantee"
    assert "Unsupported Productivity Guarantee" in issue_types

    # 2. Exaggerated Superlatives
    assert any("best productivity platform in the world" in m for m in matched_texts)
    assert any("greatest and most amazing tool ever developed" in m for m in matched_texts)

    # 3. Absolute Claims
    assert any("never need another productivity application again" in m for m in matched_texts)
    assert any("solves every business problem" in m for m in matched_texts)
    assert any("guarantees perfect results" in m for m in matched_texts)
    assert any("only platform your business will ever need" in m for m in matched_texts)

    # 4. Repeated Product Messaging
    assert any("SmartWork AI is amazing. SmartWork AI is revolutionary. SmartWork AI is the best." in m for m in matched_texts)
    assert any("Repeated Product Messaging" in t for t in issue_types)

    # 5. Duplicate or Unnecessary Promotional Sentences
    assert any("Duplicate or Unnecessary Promotional Sentence" in t for t in issue_types)
    assert any("It is the most powerful platform, the greatest platform" in m for m in matched_texts)

    # 6. Content Quality and Readability
    assert any("Content Quality & Readability" in t for t in issue_types)
    assert "brand_voice" in categories

    # Verification of scoring and severity
    assert len(issues) >= 10
    assert score == 0.0
    assert rating == "critical_violations"
    assert counts["high"] >= 4


def test_smartwork_compliant_sentence_no_false_positive(db):
    """
    Ensures the legitimate functional description within SmartWork AI is never flagged as a violation.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    compliant_sentence = (
        "SmartWork AI helps teams organize their tasks, collaborate with colleagues, and manage projects from one dashboard."
    )

    issues = run_deterministic_analysis(
        content=compliant_sentence,
        organization_id=org_id,
        db=db
    )

    assert len(issues) == 0, f"Expected 0 issues for compliant description, got: {[i['matched_text'] for i in issues]}"


def test_normal_professional_content_compliant(db):
    """
    Ensures normal professional content does not trigger false warnings, scores 100/100, and rates as compliant.
    """
    org = db.query(Organization).first()
    org_id = org.id if org else "test-org"

    professional_content = (
        "SmartWork AI provides team collaboration tools for project management and task tracking. "
        "Our platform enables distributed teams to coordinate sprint milestones, share task status updates, "
        "and streamline communication across departments. Organizations can schedule a product demonstration "
        "with our solutions team to explore enterprise integration options."
    )

    issues, score, rating, counts, _ = analyze_content(
        content=professional_content,
        organization_id=org_id,
        db=db
    )

    assert len(issues) == 0, f"Expected 0 issues for normal professional content, got: {[i['matched_text'] for i in issues]}"
    assert score == 100.0
    assert rating == "compliant"
    assert counts["critical"] == 0
    assert counts["high"] == 0


