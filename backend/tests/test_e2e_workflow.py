import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from fastapi import HTTPException

from app.core.database import Base
from app.models import User, ContentSubmission, SubmissionStatus, PublishedContent
from scripts.seed_demo import seed_demo_environment
from app.schemas.auth import UserLogin, DemoLoginRequest
from app.schemas.submission import SubmissionCreate, SubmissionUpdateContent
from app.schemas.review import ReviewDecisionRequest
from app.api.v1.endpoints.auth import demo_login
from app.api.v1.endpoints.submissions import create_submission, get_submission, update_submission_content, submit_for_review
from app.api.v1.endpoints.analysis import run_analysis
from app.api.v1.endpoints.reviews import get_review_queue, decide_submission
from app.api.v1.endpoints.publishing import publish_submission, get_public_preview


@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    # Pre-seed demo environment
    seed_demo_environment(db=session)

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_complete_brand_governance_workflow(db):
    """
    Complete End-to-End Acceptance Test for ContentGuard Brand Governance:
    1. Creator login
    2. Creator drafts content with 3 violations
    3. AI analysis identifies violations and calculates low score
    4. Creator applies fixes and re-analyzes
    5. Score rises to compliant (>= 90)
    6. Creator submits for review
    7. Reviewer inspects queue
    8. Direct publishing before approval is blocked (Rule 3)
    9. Reviewer approves submission
    10. Reviewer publishes content (Rule 4)
    11. Public read-only preview verified with actual reviewer name and score
    """

    # --- 1. Creator Login ---
    creator_auth = demo_login(req=DemoLoginRequest(role="creator"), db=db)
    assert creator_auth.user.role == "creator"
    creator = db.query(User).filter_by(id=creator_auth.user.id).first()

    # --- 2. Creator Drafts Content ---
    raw_content = (
        "Our platform offers a 100% risk-free guarantee to double your leads. "
        "ContentGuard AI uses a proprietary AI engine that processes 50,000 documents per minute."
    )
    sub_payload = SubmissionCreate(
        title="Q4 Enterprise Campaign Email",
        category="marketing_email",
        target_platform="Email Newsletter",
        campaign_name="Enterprise Launch 2026",
        content=raw_content
    )
    submission_out = create_submission(payload=sub_payload, current_user=creator, db=db)
    sub_id = submission_out.id
    assert submission_out.status == "draft"
    assert submission_out.current_content == raw_content

    # --- 3. Run AI Content Analysis ---
    report_v1 = run_analysis(submission_id=sub_id, current_user=creator, db=db)
    assert report_v1.total_issues >= 3
    assert report_v1.compliance_score < 70.0
    assert report_v1.compliance_rating in ["high_risk", "critical_violations"]

    # Check that violations were accurately flagged
    matched_phrases = [issue.matched_text for issue in report_v1.issues]
    assert any("100% risk-free guarantee" in phrase for phrase in matched_phrases)
    assert any("proprietary AI engine" in phrase for phrase in matched_phrases)
    assert any("50,000 documents per minute" in phrase for phrase in matched_phrases)

    # --- 4. Creator Corrects Copy & Saves Revision ---
    corrected_content = (
        "Our platform offers enterprise-grade reliability assurance to significantly optimize lead generation efficiency. "
        "ContentGuard AI uses ContentGuard Hybrid Governance Architecture that processes 12,000 documents per minute."
    )
    update_payload = SubmissionUpdateContent(
        content=corrected_content,
        change_summary="Replaced prohibited guarantee, buzzword, and corrected throughput specification to 12,000"
    )
    updated_sub = update_submission_content(id=sub_id, payload=update_payload, current_user=creator, db=db)
    assert len(updated_sub.versions) == 2
    assert updated_sub.current_content == corrected_content

    # --- 5. Re-Analyze Content (Score Improves) ---
    report_v2 = run_analysis(submission_id=sub_id, current_user=creator, db=db)
    assert report_v2.total_issues == 0
    assert report_v2.compliance_score >= 90.0
    assert report_v2.compliance_rating == "compliant"

    # --- 6. Creator Submits for Review ---
    submitted_review = submit_for_review(id=sub_id, current_user=creator, db=db)
    assert submitted_review.status == "pending_review"

    # --- 7. Reviewer Login & Queue Check ---
    reviewer_auth = demo_login(req=DemoLoginRequest(role="reviewer"), db=db)
    assert reviewer_auth.user.role == "reviewer"
    reviewer = db.query(User).filter_by(id=reviewer_auth.user.id).first()

    queue = get_review_queue(current_user=reviewer, db=db)
    assert any(item.id == sub_id for item in queue)

    # --- 8. Security Guard: Premature Publishing Must Fail ---
    with pytest.raises(HTTPException) as exc_info:
        publish_submission(submission_id=sub_id, current_user=reviewer, db=db)
    assert exc_info.value.status_code == 400
    assert "formally approved" in exc_info.value.detail

    # --- 9. Reviewer Approves Submission ---
    decision_payload = ReviewDecisionRequest(
        decision="approved",
        comment="All flagged issues have been verified and corrected. Approved for production."
    )
    decided_sub = decide_submission(submission_id=sub_id, payload=decision_payload, current_user=reviewer, db=db)
    assert decided_sub.status == "approved"

    # --- 10. Reviewer Publishes Approved Content ---
    pub_result = publish_submission(submission_id=sub_id, current_user=reviewer, db=db)
    assert pub_result.public_preview_token.startswith("pub_")
    assert pub_result.published_by_name == reviewer.full_name
    assert pub_result.compliance_score >= 90.0
    token = pub_result.public_preview_token

    # Verify status in database is now published
    sub_in_db = db.query(ContentSubmission).filter_by(id=sub_id).first()
    assert sub_in_db.status == "published"

    # --- 11. Public Read-Only Preview Accessible ---
    public_preview = get_public_preview(token=token, db=db)
    assert public_preview.title == "Q4 Enterprise Campaign Email"
    assert public_preview.published_by_name == reviewer.full_name
    assert public_preview.compliance_score == report_v2.compliance_score
    assert "enterprise-grade reliability assurance" in public_preview.final_content_snapshot
    assert "100% risk-free guarantee" not in public_preview.final_content_snapshot
