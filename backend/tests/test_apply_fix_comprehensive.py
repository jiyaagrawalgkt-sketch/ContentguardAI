import pytest
from app.engine.correction_engine import (
    determine_correction_strategy,
    is_instruction_or_explanation,
    locate_target_span,
    clean_grammar_after_removal,
    apply_context_aware_correction,
    validate_correction_safety,
    CorrectionValidationError,
    ManualReviewRequiredError
)
from app.models.submission import ContentSubmission, ContentVersion, SubmissionStatus
from app.models.analysis import DetectedIssue, AnalysisReport
from app.models.user import User, UserRole
from app.core.security import hash_password, create_access_token
import uuid


def test_instruction_explanation_detection():
    # Instruction phrases that must NEVER be injected into editor copy
    instructions = [
        "Substantiate promotional claims with verifiable use cases, benchmark metrics, or architectural capabilities.",
        "Provide verified research citation or remove unverified claim 'fastest in the world'.",
        "Change statement to align with approved fact: 'Official fact states 99.9% uptime'.",
        "Consult legal or compliance team for renewed documentation.",
        "Harmonize statement with verified metrics from the approved document.",
        "Consider revising this sentence to avoid regulatory scrutiny.",
    ]
    for instr in instructions:
        assert is_instruction_or_explanation(instr) is True, f"Failed to detect instruction: {instr}"

    # Legitimate copy replacements that SHOULD be allowed
    valid_replacements = [
        "transformative governance platform",
        "an advanced and highly capable enterprise platform",
        "FOR IMMEDIATE RELEASE",
        "99.9% uptime SLA",
        "processes up to 100,000 evaluations per minute",
        "contact@company.com",
    ]
    for rep in valid_replacements:
        assert is_instruction_or_explanation(rep) is False, f"False positive on valid replacement: {rep}"


def test_determine_correction_strategy():
    # 1. Removal
    strat, repl = determine_correction_strategy(action="Remove", replacement=None)
    assert strat == "REMOVE"
    assert repl == ""

    strat, repl = determine_correction_strategy(action="Replace", replacement="")
    assert strat == "REMOVE"
    assert repl == ""

    # 2. Sanitization of instruction in replacement -> fallback to MANUAL_REVIEW
    strat, repl = determine_correction_strategy(
        action="Review",
        replacement="Substantiate promotional claims with verifiable use cases, benchmark metrics, or architectural capabilities."
    )
    assert strat == "MANUAL_REVIEW"
    assert repl is None

    # 3. Clean replacement
    strat, repl = determine_correction_strategy(
        action="Replace",
        replacement="transformative platform",
        category="brand_voice"
    )
    assert strat == "REPLACE"
    assert repl == "transformative platform"

    # 4. Long rewrite in brand_voice
    strat, repl = determine_correction_strategy(
        action="Replace",
        replacement="delivers an innovative, high-performance workspace for modern engineering teams",
        category="brand_voice"
    )
    assert strat == "REWRITE"
    assert repl == "delivers an innovative, high-performance workspace for modern engineering teams"


def test_locate_target_span_and_offset_recovery():
    content = "Welcome to CloudFlow. Our platform is a game-changer for enterprise workflows."
    # 1. Exact match at initial offsets
    start = content.find("game-changer")
    end = start + len("game-changer")
    span = locate_target_span(content, "game-changer", start, end)
    assert span == (start, end)

    # 2. Shifted offsets (e.g. after an earlier edit added 10 characters at the beginning)
    shifted_content = "Extra prefix! Welcome to CloudFlow. Our platform is a game-changer for enterprise workflows."
    # Pass outdated (old) offsets
    span_recovered = locate_target_span(shifted_content, "game-changer", start, end)
    assert span_recovered == (shifted_content.find("game-changer"), shifted_content.find("game-changer") + len("game-changer"))

    # 3. Disambiguate multiple occurrences with context sentence
    multi_content = "First sentence with best solution. Later sentence with another best solution here."
    occ2_context = "Later sentence with another best solution here."
    span_multi = locate_target_span(multi_content, "best solution", context_sentence=occ2_context)
    assert span_multi is not None
    assert span_multi[0] > multi_content.find("Later sentence")


def test_clean_grammar_after_removal():
    # Dangling comma cleanup
    text1 = "Fast, reliable, and secure platform."
    # Remove "reliable, "
    raw = "Fast, , and secure platform."
    cleaned = clean_grammar_after_removal(raw, 6)
    assert ", ," not in cleaned
    assert "Fast, and secure platform." == cleaned or "Fast, secure platform." in cleaned

    # Trailing conjunction cleanup before period
    raw2 = "Engineered with superior silicon styling and ."
    cleaned2 = clean_grammar_after_removal(raw2, 40)
    assert "Engineered with superior silicon styling." == cleaned2

    # Multiple spaces collapsed
    raw3 = "Engineered with   superior   silicon styling."
    cleaned3 = clean_grammar_after_removal(raw3, 20)
    assert "Engineered with superior silicon styling." == cleaned3


def test_apply_context_aware_correction_capitalization():
    content = "Game-changer is what we built."
    corrected, op = apply_context_aware_correction(
        content=content,
        matched_text="Game-changer",
        suggested_replacement="transformative platform",
        correction_type="REPLACE"
    )
    # Notice: 'Game-changer' started with uppercase, so 'transformative' was capitalized to 'Transformative'
    assert corrected.startswith("Transformative platform")
    assert op == "REPLACE"


def test_apply_context_aware_correction_safety_rejection():
    content = "Our software has a 100% risk-free guarantee."
    # Attempting to inject an instruction MUST raise CorrectionValidationError
    with pytest.raises(CorrectionValidationError):
        apply_context_aware_correction(
            content=content,
            matched_text="100% risk-free guarantee",
            suggested_replacement="Substantiate promotional claims with verifiable use cases.",
            correction_type="REPLACE"
        )


from app.api.v1.endpoints.analysis import run_analysis, apply_fix_endpoint, ApplyFixRequest
from app.models.organization import Organization
from fastapi import HTTPException


def test_apply_fix_api_end_to_end(db):
    # Setup test organization and creator user
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="Test Corp", slug=f"testcorp-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.commit()

    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=f"creator-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Test Creator",
        role=UserRole.CREATOR.value,
        organization_id=org_id,
        hashed_password=hash_password("Secret123!"),
        is_active=True
    )
    db.add(user)
    db.commit()

    # Create submission with diverse content containing:
    # 1. Buzzword: 'game-changer'
    # 2. Redundant sentence: duplicated text
    content_initial = (
        "Enterprise DataFlow Announcement.\n\n"
        "Our data migration system is a game-changer for cloud operations.\n\n"
        "Engineered with zero latency and high throughput.\n\n"
        "Engineered with zero latency and high throughput."
    )

    sub_id = str(uuid.uuid4())
    ver_id = str(uuid.uuid4())
    sub = ContentSubmission(
        id=sub_id,
        organization_id=org_id,
        creator_id=user_id,
        title="DataFlow Release",
        status=SubmissionStatus.DRAFT.value,
        current_version_id=ver_id
    )
    ver = ContentVersion(
        id=ver_id,
        submission_id=sub_id,
        version_number=1,
        content_body=content_initial,
        change_summary="Initial draft",
        created_by=user_id
    )
    db.add(sub)
    db.add(ver)
    db.commit()

    # 1. Run initial analysis
    report_data = run_analysis(submission_id=sub_id, current_user=user, db=db)
    assert report_data.total_issues > 0
    issues = report_data.issues

    # Locate the buzzword issue
    buzz_issue = next((i for i in issues if i.matched_text == "game-changer"), None)
    assert buzz_issue is not None
    assert buzz_issue.suggested_replacement == "transformative governance platform"
    assert buzz_issue.correction_type == "REPLACE"

    # 2. Apply fix on buzzword
    req1 = ApplyFixRequest(
        issue_id=buzz_issue.id,
        matched_text=buzz_issue.matched_text,
        suggested_replacement=buzz_issue.suggested_replacement,
        correction_type=buzz_issue.correction_type
    )
    res_fix1 = apply_fix_endpoint(submission_id=sub_id, payload=req1, current_user=user, db=db)
    assert res_fix1.success is True
    assert res_fix1.applied_operation == "REPLACE"
    assert "transformative governance platform" in res_fix1.updated_content
    assert "game-changer" not in res_fix1.updated_content

    # Verify a new version was created in DB
    versions = db.query(ContentVersion).filter(ContentVersion.submission_id == sub_id).all()
    assert len(versions) == 2
    assert versions[-1].version_number == 2

    # 3. Locate the redundant duplicate sentence issue in the updated report
    updated_issues = res_fix1.report.issues
    dup_issue = next((i for i in updated_issues if "Redundant Duplicate Sentence" in i.issue_type), None)
    assert dup_issue is not None
    assert dup_issue.correction_type == "REMOVE"

    # 4. Apply fix on duplicate sentence (REMOVE)
    req2 = ApplyFixRequest(
        issue_id=dup_issue.id,
        matched_text=dup_issue.matched_text,
        suggested_replacement=dup_issue.suggested_replacement,
        correction_type=dup_issue.correction_type
    )
    res_fix2 = apply_fix_endpoint(submission_id=sub_id, payload=req2, current_user=user, db=db)
    assert res_fix2.success is True
    assert res_fix2.applied_operation == "REMOVE"

    # Verify version 3 created
    versions_after = db.query(ContentVersion).filter(ContentVersion.submission_id == sub_id).all()
    assert len(versions_after) == 3

    # 5. Verify attempting to apply fix to an already resolved issue returns 400
    with pytest.raises(HTTPException) as exc_info:
        apply_fix_endpoint(
            submission_id=sub_id,
            payload=ApplyFixRequest(issue_id=buzz_issue.id),
            current_user=user,
            db=db
        )
    assert exc_info.value.status_code == 400
    assert "already been resolved" in exc_info.value.detail.lower()


def test_advertisement_absolute_guarantee_fix(db):
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="AdCorp", slug=f"adcorp-{uuid.uuid4().hex[:6]}")
    db.add(org)
    user = User(
        id=str(uuid.uuid4()),
        email=f"creator-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Ad Creator",
        role=UserRole.CREATOR.value,
        organization_id=org_id,
        hashed_password=hash_password("Secret123!"),
        is_active=True
    )
    db.add(user)
    db.commit()

    ad_content = (
        "Discover SonicWave.\n\n"
        "Experience audio redefined. We offer a 100% risk-free guarantee on every single unit.\n\n"
        "Order yours today."
    )
    sub = ContentSubmission(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        creator_id=user.id,
        title="SonicWave Ad",
        status=SubmissionStatus.DRAFT.value,
    )
    ver = ContentVersion(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        version_number=1,
        content_body=ad_content,
        change_summary="Ad draft",
        created_by=user.id
    )
    sub.current_version_id = ver.id
    db.add(sub)
    db.add(ver)
    db.commit()

    report = run_analysis(submission_id=sub.id, current_user=user, db=db)
    guarantee_issue = next((i for i in report.issues if "guarantee" in i.matched_text.lower() or "risk-free" in i.matched_text.lower()), None)
    assert guarantee_issue is not None
    assert guarantee_issue.correction_type in ["REMOVE", "REPLACE"]

    fix_res = apply_fix_endpoint(
        submission_id=sub.id,
        payload=ApplyFixRequest(
            issue_id=guarantee_issue.id,
            matched_text=guarantee_issue.matched_text,
            suggested_replacement=guarantee_issue.suggested_replacement,
            correction_type=guarantee_issue.correction_type
        ),
        current_user=user,
        db=db
    )
    assert fix_res.success is True
    assert guarantee_issue.matched_text not in fix_res.updated_content
    # Score must improve after eliminating absolute guarantee
    assert fix_res.report.compliance_score >= report.compliance_score


def test_press_release_informal_opener_fix(db):
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="MediaCorp", slug=f"mediacorp-{uuid.uuid4().hex[:6]}")
    db.add(org)
    user = User(
        id=str(uuid.uuid4()),
        email=f"pr-{uuid.uuid4().hex[:6]}@example.com",
        full_name="PR Officer",
        role=UserRole.CREATOR.value,
        organization_id=org_id,
        hashed_password=hash_password("Secret123!"),
        is_active=True
    )
    db.add(user)
    db.commit()

    pr_content = "Hey guys, today we announce the launch of our next-generation cloud infrastructure."
    sub = ContentSubmission(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        creator_id=user.id,
        title="Q3 PR",
        category="press_release",
        status=SubmissionStatus.DRAFT.value,
    )
    ver = ContentVersion(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        version_number=1,
        content_body=pr_content,
        change_summary="PR draft",
        created_by=user.id
    )
    sub.current_version_id = ver.id
    db.add(sub)
    db.add(ver)
    db.commit()

    report = run_analysis(submission_id=sub.id, current_user=user, db=db)
    opener_issue = next((i for i in report.issues if i.matched_text == "Hey guys"), None)
    assert opener_issue is not None
    assert opener_issue.suggested_replacement == "FOR IMMEDIATE RELEASE"

    fix_res = apply_fix_endpoint(
        submission_id=sub.id,
        payload=ApplyFixRequest(
            issue_id=opener_issue.id,
            matched_text=opener_issue.matched_text,
            suggested_replacement=opener_issue.suggested_replacement,
            correction_type="REPLACE"
        ),
        current_user=user,
        db=db
    )
    assert fix_res.success is True
    assert fix_res.updated_content.startswith("FOR IMMEDIATE RELEASE")
    assert "Hey guys" not in fix_res.updated_content


def test_promotional_fluff_rejects_auto_fix_and_protects_content(db):
    org_id = str(uuid.uuid4())
    org = Organization(id=org_id, name="FluffCorp", slug=f"fluffcorp-{uuid.uuid4().hex[:6]}")
    db.add(org)
    user = User(
        id=str(uuid.uuid4()),
        email=f"copy-{uuid.uuid4().hex[:6]}@example.com",
        full_name="Copywriter",
        role=UserRole.CREATOR.value,
        organization_id=org_id,
        hashed_password=hash_password("Secret123!"),
        is_active=True
    )
    db.add(user)
    db.commit()

    # Highly hyperbolic fluff paragraph
    fluff_paragraph = (
        "Our revolutionary solution is simply unmatched and unparalleled. "
        "It provides game-changing miracles and an absolute guarantee of 100% risk-free perfection."
    )
    sub = ContentSubmission(
        id=str(uuid.uuid4()),
        organization_id=org_id,
        creator_id=user.id,
        title="Hyperbolic Pitch",
        status=SubmissionStatus.DRAFT.value,
    )
    ver = ContentVersion(
        id=str(uuid.uuid4()),
        submission_id=sub.id,
        version_number=1,
        content_body=fluff_paragraph,
        change_summary="Fluff draft",
        created_by=user.id
    )
    sub.current_version_id = ver.id
    db.add(sub)
    db.add(ver)
    db.commit()

    report = run_analysis(submission_id=sub.id, current_user=user, db=db)
    fluff_issue = next((i for i in report.issues if "Promotional Fluff" in i.issue_type), None)
    if fluff_issue:
        # Crucial assertion: the advisory sentence MUST NOT be the suggested replacement!
        assert fluff_issue.suggested_replacement is None
        assert fluff_issue.correction_type == "MANUAL_REVIEW"

        # Attempting to auto-apply fix on manual review issue MUST raise HTTP 400
        with pytest.raises(HTTPException) as exc_info:
            apply_fix_endpoint(
                submission_id=sub.id,
                payload=ApplyFixRequest(issue_id=fluff_issue.id),
                current_user=user,
                db=db
            )
        assert exc_info.value.status_code == 400
        assert "manual editorial review" in exc_info.value.detail.lower()

        # Content in DB must be untouched and NOT contain "Substantiate promotional claims"
        refreshed_ver = db.query(ContentVersion).filter(ContentVersion.id == ver.id).first()
        assert "Substantiate promotional claims" not in refreshed_ver.content_body
        assert refreshed_ver.content_body == fluff_paragraph

