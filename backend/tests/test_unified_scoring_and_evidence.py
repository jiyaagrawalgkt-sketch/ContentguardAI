import pytest
import uuid
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.brand_knowledge import ApprovedFact
from app.api.v1.endpoints.analysis import run_analysis
from scripts.seed_demo import seed_demo_environment


def test_unified_scoring_penalizes_unsupported_claim(db):
    """
    Validates Part 2: If content has an unsupported claim,
    the unified analysis engine penalizes evidence confidence and caps overall score below 100.
    """
    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()
    assert creator is not None

    # Create submission with an UNVERIFIED scale assertion (e.g. 50,000 servers which is not in knowledge base)
    sub_id = str(uuid.uuid4())
    submission = ContentSubmission(
        id=sub_id,
        organization_id=creator.organization_id,
        creator_id=creator.id,
        title="Unverified Scale Campaign",
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
        content_body="Our cloud architecture reliably spans over 50,000 active enterprises worldwide without interruption.",
        change_summary="Initial copy with unverified metric",
    )
    db.add(version)
    submission.current_version_id = ver_id
    db.commit()

    # Run unified analysis
    report = run_analysis(submission_id=sub_id, current_user=creator, db=db)

    # Validate that Evidence Confidence is NOT 100
    assert report.evidence_confidence_score < 100.0, "Evidence score must be penalized for uncorroborated metric"
    # Validate that Overall Score is NOT 100
    assert report.compliance_score < 100.0, "Overall score must not be 100 when an unverified metric exists"
    assert report.publication_risk in ["medium", "high", "critical"]

    # Validate that the unsupported claim appears in issues findings
    unverified_issues = [i for i in report.issues if "Evidence" in i.issue_type or i.category == "misleading_claim"]
    assert len(unverified_issues) > 0, "Unsupported claim must appear as actionable finding"


def test_unified_scoring_rewards_supported_claim(db):
    """
    Validates that when a claim is backed by the approved fact vault (99.9% uptime SLA),
    it is marked SUPPORTED and achieves full evidence confidence.
    """
    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()

    sub_id = str(uuid.uuid4())
    submission = ContentSubmission(
        id=sub_id,
        organization_id=creator.organization_id,
        creator_id=creator.id,
        title="Verified SLA Copy",
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
        content_body="ContentGuard AI provides a 99.9% uptime SLA backed by SOC-2 Type II certified enterprise infrastructure.",
        change_summary="Fully compliant verified copy",
    )
    db.add(version)
    submission.current_version_id = ver_id
    db.commit()

    report = run_analysis(submission_id=sub_id, current_user=creator, db=db)

    # In seed_demo.py, 99.9% uptime SLA is an ApprovedFact!
    assert report.evidence_confidence_score == 100.0, "Evidence score must be 100 for verified facts"
    assert report.compliance_score >= 90.0
