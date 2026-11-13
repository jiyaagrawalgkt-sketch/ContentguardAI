import io
import pytest
import uuid
from PIL import Image
from unittest.mock import MagicMock
from app.models.user import User
from app.models.submission import ContentSubmission, SubmissionStatus
from app.models.multimodal import VisualAnalysisReport
from app.models.publication import PublishedContent
from app.api.v1.endpoints.multimodal import (
    analyze_visual_endpoint,
    submit_visual_for_review,
    decide_visual_review,
    publish_visual_report,
)
from app.api.v1.endpoints.reviews import get_review_queue
from app.api.v1.endpoints.publishing import (
    publish_submission,
    get_pre_publication_gate_status,
    get_public_preview,
    get_preview_by_submission,
)
from scripts.seed_demo import seed_demo_environment


def _create_synthetic_image_bytes(color=(40, 60, 120)) -> bytes:
    img = Image.new("RGB", (400, 300), color=color)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def test_visual_review_complete_lifecycle(db):
    """
    End-to-end verification of the visual governance workflow:
    1. Creator uploads visual asset -> auto-creates submission & ContentVersion with OCR/metadata.
    2. Visual status is analysis_complete.
    3. Creator submits visual for review -> transitions submission & report to PENDING_REVIEW.
    4. Reviewer inspects queue -> visual submission appears with visual_score as compliance_score.
    5. Reviewer requests changes -> transitions to CHANGES_REQUESTED with feedback recorded.
    6. Creator resubmits with notes -> returns to PENDING_REVIEW.
    7. Reviewer approves -> transitions to APPROVED, is_published remains FALSE (separate approval).
    8. Authorized publishing -> transitions to PUBLISHED, generates public preview token, is_published TRUE.
    9. Public preview endpoint verifies published content and token access.
    """
    seed_demo_environment(db=db)

    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()
    reviewer = db.query(User).filter(User.email == "reviewer@contentguard.demo").first()
    assert creator is not None
    assert reviewer is not None

    # Step 1: Upload and Analyze Visual Asset
    img_bytes = _create_synthetic_image_bytes()
    upload_mock = MagicMock()
    upload_mock.filename = "marketing_banner_q4.png"
    upload_mock.content_type = "image/png"
    upload_mock.file = io.BytesIO(img_bytes)

    analysis_res = analyze_visual_endpoint(
        file=upload_mock,
        submission_id=None,
        alt_text="Q4 Product Announcement Banner",
        title="Q4 Banner Visual Asset",
        current_user=creator,
        db=db,
    )

    report_id = analysis_res["report_id"]
    sub_id = analysis_res["submission_id"]
    assert report_id is not None
    assert sub_id is not None

    sub = db.query(ContentSubmission).filter(ContentSubmission.id == sub_id).first()
    assert sub is not None
    assert sub.status == SubmissionStatus.ANALYSIS_COMPLETE.value
    assert len(sub.versions) >= 1
    assert sub.current_version_id is not None
    assert "[Visual Brand Asset: marketing_banner_q4.png]" in sub.versions[0].content_body

    # Step 2: Submit for Reviewer Approval
    submit_res = submit_visual_for_review(
        report_id=report_id,
        payload={"notes": "Please verify WCAG 2.1 AA compliance for Q4 global launch."},
        current_user=creator,
        db=db,
    )
    assert submit_res["review_status"] == "pending_review"

    db.refresh(sub)
    assert sub.status == SubmissionStatus.PENDING_REVIEW.value

    # Step 3: Reviewer Queue Verification
    queue_items = get_review_queue(status_filter=None, current_user=reviewer, db=db)
    target_item = next((item for item in queue_items if item.id == sub_id), None)
    assert target_item is not None
    assert target_item.status == SubmissionStatus.PENDING_REVIEW.value
    assert target_item.compliance_score is not None
    assert target_item.compliance_score == analysis_res["visual_score"]

    # Step 4: Pre-Publication Gate Check (Should block before approval)
    gate_before = get_pre_publication_gate_status(
        submission_id=sub_id,
        current_user=reviewer,
        db=db,
    )
    assert gate_before["can_publish"] is False
    assert gate_before["gate_status"] == "awaiting_review"

    # Step 5: Reviewer Requests Changes
    change_res = decide_visual_review(
        report_id=report_id,
        payload={
            "decision": "changes_requested",
            "comment": "Contrast on text overlay is slightly low. Please apply AA contrast enhancement."
        },
        current_user=reviewer,
        db=db,
    )
    assert change_res["review_status"] == "changes_requested"
    assert change_res["is_published"] is False

    db.refresh(sub)
    assert sub.status == SubmissionStatus.CHANGES_REQUESTED.value

    # Step 6: Creator Re-submits After Corrections
    resubmit_res = submit_visual_for_review(
        report_id=report_id,
        payload={"notes": "Applied accepted WCAG contrast fixes. Ready for re-audit."},
        current_user=creator,
        db=db,
    )
    assert resubmit_res["review_status"] == "pending_review"

    db.refresh(sub)
    assert sub.status == SubmissionStatus.PENDING_REVIEW.value

    # Step 7: Reviewer Approves (Explicitly separate from publishing)
    approve_res = decide_visual_review(
        report_id=report_id,
        payload={
            "decision": "approved",
            "comment": "Brand palette match and contrast verified. Approved for publication."
        },
        current_user=reviewer,
        db=db,
    )
    assert approve_res["review_status"] == "approved"
    # IMPORTANT: Approval alone must NOT mark as published!
    assert approve_res["is_published"] is False

    db.refresh(sub)
    assert sub.status == SubmissionStatus.APPROVED.value

    # Gate status should now allow publishing
    gate_approved = get_pre_publication_gate_status(
        submission_id=sub_id,
        current_user=reviewer,
        db=db,
    )
    assert gate_approved["can_publish"] is True
    assert gate_approved["gate_status"] == "approved_for_publication"

    # Step 8: Explicit Publishing Action
    publish_res = publish_submission(
        submission_id=sub_id,
        current_user=reviewer,
        db=db,
    )
    assert publish_res.public_preview_token is not None

    db.refresh(sub)
    assert sub.status == SubmissionStatus.PUBLISHED.value

    rep = db.query(VisualAnalysisReport).filter(VisualAnalysisReport.id == report_id).first()
    assert rep.is_published is True
    assert rep.published_at is not None

    # Step 9: Public Preview Verification
    preview = get_public_preview(token=publish_res.public_preview_token, db=db)
    assert preview.title == sub.title
    assert preview.published_by_name == reviewer.full_name
    assert preview.compliance_score == rep.visual_score

    # Preview by submission ID endpoint verification
    sub_preview = get_preview_by_submission(submission_id=sub_id, current_user=creator, db=db)
    assert sub_preview.public_preview_token == publish_res.public_preview_token
