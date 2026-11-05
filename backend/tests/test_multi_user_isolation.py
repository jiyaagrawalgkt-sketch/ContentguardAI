import pytest
from fastapi import HTTPException
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.core.security import hash_password
from app.schemas.auth import UserRegister
from app.schemas.submission import SubmissionCreate
from app.schemas.review import ReviewDecisionRequest
from app.api.v1.endpoints.auth import register
from app.api.v1.endpoints.submissions import list_submissions, get_submission, create_submission
from app.api.v1.endpoints.reviews import get_review_queue, decide_submission


def test_registration_multiple_accounts_and_uniqueness(db):
    """
    Verifies that multiple users can register with unique emails and each gets
    a distinct ID, and attempting to register an existing email is rejected.
    """
    # 1. Register Creator 1
    reg1 = UserRegister(
        email="creator1@contentguard.test",
        password="Password123!",
        full_name="Creator One",
        role="creator",
        organization_name="Enterprise Alpha"
    )
    res1 = register(user_in=reg1, db=db)
    assert res1.user.email == "creator1@contentguard.test"
    user1_id = res1.user.id

    # 2. Register Creator 2 with different email
    reg2 = UserRegister(
        email="creator2@contentguard.test",
        password="Password123!",
        full_name="Creator Two",
        role="creator",
        organization_name="Enterprise Beta"
    )
    res2 = register(user_in=reg2, db=db)
    assert res2.user.email == "creator2@contentguard.test"
    user2_id = res2.user.id
    assert user1_id != user2_id

    # 3. Duplicate email registration rejected
    dup_reg = UserRegister(
        email="CREATOR1@contentguard.test",  # case-insensitive check
        password="DifferentPass123!",
        full_name="Impostor",
        role="creator"
    )
    with pytest.raises(HTTPException) as exc_info:
        register(user_in=dup_reg, db=db)
    assert exc_info.value.status_code == 400


def test_cross_creator_data_isolation(db):
    """
    Verifies that Creator 1 and Creator 2 are completely isolated:
    Creator 2 cannot see Creator 1's submissions in the dashboard,
    and cannot retrieve Creator 1's submission details directly.
    """
    org = Organization(id="org-shared", name="Shared Workspace Org", slug="shared-org")
    db.add(org)

    creator1 = User(
        id="usr-c1",
        organization_id=org.id,
        email="creator1@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Creator 1",
        role=UserRole.CREATOR.value,
        is_active=True
    )
    creator2 = User(
        id="usr-c2",
        organization_id=org.id,
        email="creator2@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Creator 2",
        role=UserRole.CREATOR.value,
        is_active=True
    )
    db.add_all([creator1, creator2])
    db.commit()

    # Creator 1 creates a private submission
    payload1 = SubmissionCreate(
        title="Creator 1 Confidential Draft",
        category="marketing_email",
        content="Confidential marketing campaign draft for Q4 launch."
    )
    sub1_out = create_submission(payload=payload1, current_user=creator1, db=db)

    # 1. Creator 1 sees their submission
    subs_c1 = list_submissions(current_user=creator1, db=db)
    assert len(subs_c1) == 1
    assert subs_c1[0].id == sub1_out.id

    # 2. Creator 2 CANNOT see Creator 1's submission in their dashboard list
    subs_c2 = list_submissions(current_user=creator2, db=db)
    assert len(subs_c2) == 0

    # 3. Creator 2 CANNOT fetch Creator 1's submission by ID (HTTP 403 Forbidden)
    with pytest.raises(HTTPException) as exc_info:
        get_submission(id=sub1_out.id, current_user=creator2, db=db)
    assert exc_info.value.status_code == 403


def test_reviewer_queue_and_self_approval_prevention(db):
    """
    Verifies that Reviewers can access organization submissions,
    but cannot approve their own submissions (Conflict of Interest prevention).
    """
    org = Organization(id="org-rev-test", name="Governance Org", slug="gov-org")
    db.add(org)

    creator1 = User(
        id="usr-creator-only",
        organization_id=org.id,
        email="creator1@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Content Author",
        role=UserRole.CREATOR.value,
        is_active=True
    )
    reviewer = User(
        id="usr-reviewer-only",
        organization_id=org.id,
        email="reviewer@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Samantha Reviewer",
        role=UserRole.REVIEWER.value,
        is_active=True
    )
    db.add_all([creator1, reviewer])
    db.commit()

    # Creator submits content
    sub = ContentSubmission(
        id="sub-gov-1",
        organization_id=org.id,
        creator_id=creator1.id,
        title="Campaign for Review",
        category="advertisement",
        status=SubmissionStatus.PENDING_REVIEW.value
    )
    v1 = ContentVersion(
        id="v1-gov",
        submission_id=sub.id,
        version_number=1,
        content_body="Promotional copy awaiting reviewer clearance.",
        created_by=creator1.id
    )
    db.add_all([sub, v1])
    db.commit()

    # Reviewer inspects queue
    queue = get_review_queue(current_user=reviewer, db=db)
    assert len(queue) == 1
    assert queue[0].id == sub.id

    # Reviewer approves submission successfully
    decision_req = ReviewDecisionRequest(decision="approved", comment="Approved for distribution.")
    approved_sub = decide_submission(submission_id=sub.id, payload=decision_req, current_user=reviewer, db=db)
    assert approved_sub.status == SubmissionStatus.APPROVED.value

    # CONFLICT OF INTEREST: Reviewer creates their own submission and tries to approve it
    reviewer_own_sub = ContentSubmission(
        id="sub-reviewer-own",
        organization_id=org.id,
        creator_id=reviewer.id,
        title="Reviewer Self Post",
        category="marketing_email",
        status=SubmissionStatus.PENDING_REVIEW.value
    )
    db.add(reviewer_own_sub)
    db.commit()

    with pytest.raises(HTTPException) as exc_info:
        decide_submission(submission_id=reviewer_own_sub.id, payload=decision_req, current_user=reviewer, db=db)
    assert exc_info.value.status_code == 403
    assert "Conflict of interest" in exc_info.value.detail


def test_cross_organization_data_isolation(db):
    """
    Verifies that Organization A and Organization B are strictly isolated:
    A Reviewer in Org B cannot see submissions from Org A.
    """
    org_a = Organization(id="org-a", name="Org Alpha", slug="org-a")
    org_b = Organization(id="org-b", name="Org Beta", slug="org-b")
    db.add_all([org_a, org_b])

    creator_a = User(
        id="usr-ca",
        organization_id=org_a.id,
        email="creator_a@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Creator Alpha",
        role=UserRole.CREATOR.value,
        is_active=True
    )
    reviewer_b = User(
        id="usr-rb",
        organization_id=org_b.id,
        email="reviewer_b@contentguard.test",
        hashed_password=hash_password("Pass123!"),
        full_name="Reviewer Beta",
        role=UserRole.REVIEWER.value,
        is_active=True
    )
    db.add_all([creator_a, reviewer_b])

    sub_a = ContentSubmission(
        id="sub-alpha",
        organization_id=org_a.id,
        creator_id=creator_a.id,
        title="Confidential Alpha Launch",
        category="landing_page",
        status=SubmissionStatus.PENDING_REVIEW.value
    )
    db.add(sub_a)
    db.commit()

    # Reviewer B in Org B inspects queue -> Must NOT see Org A submission
    queue_b = get_review_queue(current_user=reviewer_b, db=db)
    assert len(queue_b) == 0

    # Reviewer B cannot decide on Org A submission (HTTP 404)
    decision_req = ReviewDecisionRequest(decision="approved", comment="Illegal cross-org approval")
    with pytest.raises(HTTPException) as exc_info:
        decide_submission(submission_id=sub_a.id, payload=decision_req, current_user=reviewer_b, db=db)
    assert exc_info.value.status_code == 404
