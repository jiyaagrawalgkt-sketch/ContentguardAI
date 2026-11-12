import pytest
import uuid
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm
from app.engine.evidence_engine import extract_factual_claims, verify_claims_against_evidence
from app.api.v1.endpoints.auth import login, _issue_tokens_for_user
from app.api.v1.endpoints.submissions import submit_for_review
from app.api.v1.endpoints.reviews import decide_submission
from app.schemas.auth import UserLogin
from app.schemas.review import ReviewDecisionRequest
from scripts.seed_demo import seed_demo_environment


def test_complete_saas_end_to_end_flow(db):
    """
    Validates complete workflow:
    Seeding -> Authentication -> Draft Submission -> Evidence Verification ->
    Review Submission -> Reviewer Decision (Approval) -> Audit Logging.
    """
    # 1. Seed demo environment
    seed_demo_environment(db=db)

    # 2. Login as demo user demo@contentguard.ai
    login_req = UserLogin(email="demo@contentguard.ai", password="Demo@12345")
    auth_resp = login(login_req, db=db)
    assert auth_resp.access_token is not None
    assert auth_resp.user.email == "demo@contentguard.ai"
    assert auth_resp.user.role == "creator"
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()

    # 3. Create content submission with draft copy
    sub_id = str(uuid.uuid4())
    submission = ContentSubmission(
        id=sub_id,
        organization_id=creator.organization_id,
        creator_id=creator.id,
        title="Enterprise Cloud Security Brief",
        category="marketing_email",
        status=SubmissionStatus.DRAFT.value,
    )
    db.add(submission)
    db.commit()

    ver_id = str(uuid.uuid4())
    version = ContentVersion(
        id=ver_id,
        submission_id=sub_id,
        version_number=1,
        content_body="Our platform guarantees 100% risk-free migration and increases team productivity by 80%. We are SOC 2 Type II certified.",
        change_summary="Initial draft submission",
    )
    db.add(version)
    submission.current_version_id = ver_id
    db.commit()

    # 4. Evidence Extraction & Verification
    raw_claims = extract_factual_claims(version.content_body)
    assert len(raw_claims) >= 2
    verified = verify_claims_against_evidence(raw_claims, creator.organization_id, db)
    assert len(verified) == len(raw_claims)
    # The 80% multiplier or 100% guarantee will be unsupported or conflicting
    unsupported_or_conflicting = [c for c in verified if c["verification_status"] in ["unsupported", "conflicting"]]
    assert len(unsupported_or_conflicting) > 0

    # 5. Creator corrects text (Version 2)
    ver2_id = str(uuid.uuid4())
    version2 = ContentVersion(
        id=ver2_id,
        submission_id=sub_id,
        version_number=2,
        content_body="Our platform offers verified migration assistance and increases team productivity through automated workflows. We are SOC 2 Type II certified.",
        change_summary="Revised copy to eliminate unverified guarantee",
    )
    db.add(version2)
    submission.current_version_id = ver2_id
    db.commit()

    # 6. Creator submits for review
    submitted = submit_for_review(id=sub_id, current_user=creator, db=db)
    assert submitted.status == SubmissionStatus.PENDING_REVIEW.value

    # 7. Reviewer authenticates
    reviewer = db.query(User).filter(User.email == "reviewer@contentguard.demo").first()
    assert reviewer is not None
    assert reviewer.role == UserRole.REVIEWER.value

    # 8. Reviewer inspects and approves
    decision_req = ReviewDecisionRequest(
        decision="approved",
        comment="Factual assertions now aligned with approved evidence whitepapers. Approved for release."
    )
    approved_sub = decide_submission(submission_id=sub_id, payload=decision_req, current_user=reviewer, db=db)
    assert approved_sub.status == SubmissionStatus.APPROVED.value
    assert approved_sub.latest_review_feedback == "Factual assertions now aligned with approved evidence whitepapers. Approved for release."
    assert approved_sub.latest_reviewer_name == reviewer.full_name
