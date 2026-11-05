import pytest
import uuid
from datetime import datetime, timezone, date
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.models import (
    Organization,
    User,
    UserRole,
    BrandGuideline,
    ApprovedFact,
    RestrictedTerm,
    BrandAsset,
    ContentSubmission,
    UploadedFile,
    ContentVersion,
    SubmissionStatus,
    ContentCategory,
    AnalysisReport,
    DetectedIssue,
    CorrectionSuggestion,
    EngineMode,
    ComplianceRating,
    IssueModule,
    IssueSeverity,
    ReviewComment,
    ApprovalRecord,
    ReviewDecision,
    PublishedContent,
    AuditLog,
)

# Test-specific SQLite database to verify all 16 tables
TEST_DB_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_session():
    engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    
    # Enforce foreign key constraints
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_all_16_tables_exist(db_session):
    """Verify that all 16 required tables exist in metadata."""
    expected_tables = {
        "organizations",
        "users",
        "brand_guidelines",
        "approved_facts",
        "restricted_terms",
        "brand_assets",
        "content_submissions",
        "uploaded_files",
        "content_versions",
        "analysis_reports",
        "detected_issues",
        "correction_suggestions",
        "review_comments",
        "approval_records",
        "published_content",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"


def test_complete_governance_data_flow(db_session):
    """
    Test relational persistence and cascade behavior across the entire data model:
    Org -> User -> Guidelines -> Facts -> Restricted -> Assets -> Submission -> Versions -> Report -> Issues -> Suggestions -> Review -> Publish -> Audit
    """
    # 1. Organization
    org = Organization(
        name="Acme Corporation",
        slug="acme-corp",
        industry="Enterprise Software"
    )
    db_session.add(org)
    db_session.commit()
    assert org.id is not None

    # 2. Users (Creator, Reviewer, Admin)
    creator = User(
        organization_id=org.id,
        email="creator@acme.demo",
        hashed_password="hashed_pw_demo",
        full_name="Alice Creator",
        role=UserRole.CREATOR.value
    )
    reviewer = User(
        organization_id=org.id,
        email="reviewer@acme.demo",
        hashed_password="hashed_pw_demo",
        full_name="Bob Reviewer",
        role=UserRole.REVIEWER.value
    )
    admin = User(
        organization_id=org.id,
        email="admin@acme.demo",
        hashed_password="hashed_pw_demo",
        full_name="Carol Admin",
        role=UserRole.ADMIN.value
    )
    db_session.add_all([creator, reviewer, admin])
    db_session.commit()

    # 3. Brand Knowledge
    guideline = BrandGuideline(
        organization_id=org.id,
        category="tone_voice",
        title="Authoritative yet approachable",
        description="Write clearly without tech buzzwords",
        rules=["Never use 100% guarantee", "Avoid proprietary jargon"],
        severity_level="high"
    )
    fact = ApprovedFact(
        organization_id=org.id,
        topic="Platform Performance",
        statement="ContentGuard AI processes 12,000 documents per minute with 99.9% uptime",
        verified_numbers={"docs_per_min": 12000, "uptime_percent": 99.9},
        reference_url_or_doc="https://acme.com/soc2-audit.pdf"
    )
    restricted = RestrictedTerm(
        organization_id=org.id,
        term="risk-free guarantee",
        category="prohibited",
        severity="critical",
        suggested_alternative="verified reliability",
        reason="Absolute guarantees violate compliance policy 4.2"
    )
    asset = BrandAsset(
        organization_id=org.id,
        name="Official Brand Palette",
        asset_type="color_palette",
        primary_color_hex="#0B0F19",
        secondary_color_hex="#6366F1",
        accent_color_hex="#FAF9FF"
    )
    db_session.add_all([guideline, fact, restricted, asset])
    db_session.commit()

    # 4. Content Submission & Uploaded File
    submission = ContentSubmission(
        organization_id=org.id,
        creator_id=creator.id,
        title="Q4 Product Launch Announcement",
        category=ContentCategory.MARKETING_EMAIL.value,
        target_platform="Email Newsletter",
        campaign_name="Enterprise Launch 2026",
        status=SubmissionStatus.DRAFT.value
    )
    db_session.add(submission)
    db_session.commit()

    uploaded = UploadedFile(
        submission_id=submission.id,
        original_filename="launch_draft.docx",
        stored_path="/uploads/launch_draft.docx",
        mime_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        file_size_bytes=10240,
        extracted_text="Our platform offers a risk-free guarantee to double your leads."
    )
    db_session.add(uploaded)
    db_session.commit()

    # 5. Content Version
    version1 = ContentVersion(
        submission_id=submission.id,
        version_number=1,
        content_body="Our platform offers a risk-free guarantee to double your leads.",
        change_summary="Initial draft",
        created_by=creator.id
    )
    db_session.add(version1)
    db_session.commit()
    submission.current_version_id = version1.id
    db_session.commit()

    # 6. Analysis Report & Issues
    report = AnalysisReport(
        submission_id=submission.id,
        version_id=version1.id,
        engine_mode=EngineMode.DETERMINISTIC_FALLBACK.value,
        compliance_score=68.0,
        compliance_rating=ComplianceRating.NEEDS_REVIEW.value,
        total_issues=1,
        critical_count=1,
        summary_verdict="Found 1 critical violation regarding prohibited guarantee terminology."
    )
    db_session.add(report)
    db_session.commit()

    issue = DetectedIssue(
        report_id=report.id,
        module=IssueModule.RESTRICTED_LANGUAGE.value,
        severity=IssueSeverity.CRITICAL.value,
        issue_type="Prohibited Guarantee",
        matched_text="risk-free guarantee",
        char_start=24,
        char_end=43,
        explanation="Violates Policy 4.2",
        guideline_reference="Brand Guideline: Tone & Policy",
        confidence=1.0
    )
    db_session.add(issue)
    db_session.commit()

    suggestion = CorrectionSuggestion(
        issue_id=issue.id,
        original_text="risk-free guarantee",
        suggested_replacement="verified reliability",
        rationale="Complies with marketing policy",
        is_accepted=True
    )
    db_session.add(suggestion)
    db_session.commit()

    # 7. Content Revision (Version 2 after accepting AI fix)
    version2 = ContentVersion(
        submission_id=submission.id,
        version_number=2,
        content_body="Our platform offers verified reliability to double your leads.",
        change_summary="Accepted AI suggested fix for risk-free guarantee",
        created_by=creator.id
    )
    db_session.add(version2)
    db_session.commit()
    submission.current_version_id = version2.id
    submission.status = SubmissionStatus.PENDING_REVIEW.value
    db_session.commit()

    # 8. Human Review Comments & Approval
    comment = ReviewComment(
        submission_id=submission.id,
        reviewer_id=reviewer.id,
        comment_text="Revised copy is compliant with brand guidelines. Approved for publication.",
        is_internal_only=False
    )
    approval = ApprovalRecord(
        submission_id=submission.id,
        reviewer_id=reviewer.id,
        decision=ReviewDecision.APPROVED.value,
        feedback_reason="All violations addressed",
        compliance_score_at_approval=95.0
    )
    submission.status = SubmissionStatus.APPROVED.value
    db_session.add_all([comment, approval])
    db_session.commit()

    # 9. Published Content
    token = "pub_" + uuid.uuid4().hex
    published = PublishedContent(
        submission_id=submission.id,
        public_preview_token=token,
        published_by=reviewer.id,
        final_content_snapshot=version2.content_body,
        public_access_enabled=True
    )
    submission.status = SubmissionStatus.PUBLISHED.value
    db_session.add(published)
    db_session.commit()

    # 10. Audit Log
    audit = AuditLog(
        organization_id=org.id,
        user_id=reviewer.id,
        action="CONTENT_PUBLISHED",
        entity_type="content_submission",
        entity_id=submission.id,
        details={"token": token, "version": 2}
    )
    db_session.add(audit)
    db_session.commit()

    # Verifications
    assert submission.status == SubmissionStatus.PUBLISHED.value
    assert submission.published_content.public_preview_token == token
    assert len(submission.versions) == 2
    assert submission.review_comments[0].reviewer.full_name == "Bob Reviewer"
    assert org.users[0].full_name in ["Alice Creator", "Bob Reviewer", "Carol Admin"]
    assert audit.action == "CONTENT_PUBLISHED"


def test_cascade_deletion(db_session):
    """Verify that deleting an organization cascades down cleanly to all owned records."""
    org = Organization(name="Delete Me Corp", slug="delete-me")
    db_session.add(org)
    db_session.commit()

    creator = User(
        organization_id=org.id,
        email="delete_user@acme.demo",
        hashed_password="pw",
        full_name="Doomed User",
        role="creator"
    )
    db_session.add(creator)
    db_session.commit()

    submission = ContentSubmission(
        organization_id=org.id,
        creator_id=creator.id,
        title="Doomed Submission",
        category="blog",
        status="draft"
    )
    db_session.add(submission)
    db_session.commit()

    # Deleting organization must delete submission and user
    db_session.delete(org)
    db_session.commit()

    assert db_session.query(Organization).filter_by(id=org.id).first() is None
    assert db_session.query(User).filter_by(id=creator.id).first() is None
    assert db_session.query(ContentSubmission).filter_by(id=submission.id).first() is None
