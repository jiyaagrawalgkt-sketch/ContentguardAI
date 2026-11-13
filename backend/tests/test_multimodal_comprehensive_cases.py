import io
import os
import tempfile
import pytest
from PIL import Image

from app.engine.multimodal_engine import (
    analyze_visual_asset,
    generate_corrected_visual_asset,
    verify_corrected_visual_asset,
    synthesize_sample_preset_image,
    SAMPLE_PRESETS_METADATA,
    VERIFIED_BRAND_REGISTRY,
    WCAGComplianceLevel,
)


def test_sample_presets_metadata_structure():
    """Verify all 4 sample presets are present with complete metadata and violations preview."""
    assert len(SAMPLE_PRESETS_METADATA) == 4
    preset_ids = [p["id"] for p in SAMPLE_PRESETS_METADATA]
    assert "pepsi-campaign-poster" in preset_ids
    assert "apple-certified-card" in preset_ids
    assert "lg-display-banner" in preset_ids
    assert "enterprise-launch-poster" in preset_ids

    for preset in SAMPLE_PRESETS_METADATA:
        assert preset["title"]
        assert preset["badge"]
        assert preset["brand"]
        assert preset["description"]
        assert len(preset["violations_preview"]) >= 2


def test_pepsi_campaign_poster_synthesis_and_complete_multimodal_report():
    """
    Test Case 1: Image 1 Specification Sheet Scenario.
    Marketing employee uploads a poster with an outdated/purple Pepsi logo + conflicting claim.
    ContentGuard AI identifies ALL 4 categories in ONE unified report:
    1. Logo Mismatch / Unapproved Color
    2. Off-Brand Colour Usage
    3. Unsupported Promotional Claim (#1 in the world with 100% guarantee)
    4. Accessibility Contrast Issue (WCAG 2.1 FAIL)
    Plus copy typo ('revalutionary').
    """
    img_bytes, filename, title, alt_text = synthesize_sample_preset_image("pepsi-campaign-poster")
    assert img_bytes is not None and len(img_bytes) > 1000
    assert filename == "pepsi_multimodal_campaign_poster.png"
    assert "Pepsi" in title

    # Run complete multimodal analysis
    analysis = analyze_visual_asset(
        image_bytes=img_bytes,
        alt_text=alt_text
    )

    assert analysis["image_width"] == 600
    assert analysis["image_height"] == 600
    assert analysis["aspect_ratio"] == "1.0:1"

    # Brand recognized as Pepsi
    assert analysis["detected_logo_name"] and analysis["detected_logo_name"].lower() == "pepsi"

    issues = analysis["visual_issues"]
    categories = [iss.get("category") for iss in issues]
    issue_types = [iss.get("type") for iss in issues]

    # Category 1: Logo Mismatch / Modified Brand Color
    assert "logo_integrity" in categories or any("logo" in t for t in issue_types)
    logo_iss = next(iss for iss in issues if iss.get("category") == "logo_integrity" or "logo" in iss.get("type", ""))
    assert "pepsi" in logo_iss["title"].lower() or "pepsi" in logo_iss["detected_element"].lower()
    assert logo_iss["detected_element"]
    assert logo_iss["expected_reference"]
    assert logo_iss["explanation"]
    assert logo_iss["suggestion"]

    # Category 2: Off-Brand Colour Usage
    assert "brand_palette" in categories or any("color" in t for t in issue_types)
    color_iss = next(iss for iss in issues if iss.get("category") == "brand_palette" or "off_brand_color" in iss.get("type", ""))
    assert color_iss["detected_element"]
    assert "pepsi" in color_iss["expected_reference"].lower()
    assert color_iss["explanation"]

    # Category 3: Unsupported Promotional Claim
    assert "claims_promotional" in categories or any("claim" in t for t in issue_types)
    claim_issues = [iss for iss in issues if iss.get("category") == "claims_promotional" or "claim" in iss.get("type", "")]
    assert len(claim_issues) >= 1
    assert any("100% guarantee" in iss["title"].lower() or "#1 in the world" in iss["title"].lower() for iss in claim_issues)
    for c_iss in claim_issues:
        assert c_iss["detected_element"]
        assert c_iss["expected_reference"]

    # Category 4: Accessibility Contrast Issue
    assert analysis["wcag_compliance"] == WCAGComplianceLevel.FAIL.value
    assert "accessibility" in categories
    contrast_iss = next(iss for iss in issues if iss.get("type") == "contrast_failure")
    assert contrast_iss["contrast_ratio"] if "contrast_ratio" in contrast_iss else "contrast" in contrast_iss["title"].lower()
    assert contrast_iss["detected_element"]
    assert contrast_iss["expected_reference"]

    # Extra: Typo in copy
    assert any("revalutionary" in iss.get("title", "").lower() or "revalutionary" in iss.get("detected_element", "").lower() for iss in issues)


def test_pepsi_poster_apply_fix_and_independent_verification():
    """
    Test Case 2: Apply Fix on the Pepsi Campaign Poster.
    Accepting corrections must:
    1. Replace the purple logo with the official canonical Pepsi globe (#004B93 blue, #C9002B red, white wave ribbon).
    2. Enhance contrast.
    3. Pass independent post-correction verification with >= 85% unaffected area preservation.
    4. Guard against alien brand intrusion (no LinkedIn blue).
    """
    img_bytes, filename, title, alt_text = synthesize_sample_preset_image("pepsi-campaign-poster")
    analysis = analyze_visual_asset(image_bytes=img_bytes, alt_text=alt_text)

    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "orig_pepsi.png")
        corr_path = os.path.join(tmpdir, "corr_pepsi.png")

        with open(orig_path, "wb") as f:
            f.write(img_bytes)

        # Accept all detected corrections
        accepted_ids = [iss["id"] for iss in analysis["visual_issues"]]

        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=accepted_ids,
            visual_issues=analysis["visual_issues"]
        )

        assert res["success"] is True
        assert os.path.exists(corr_path)

        # Independently audit the corrected graphic
        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            visual_issues=analysis["visual_issues"],
            accepted_corrections=accepted_ids,
            brand_name="Pepsi"
        )

        assert audit["passed"] is True
        assert audit["status"] == "verified"
        assert audit["status_headline"] == "CORRECTED & VERIFIED"

        check_names = [c["name"] for c in audit["checks"]]
        assert "Canvas Dimension & Resolution Integrity" in check_names
        assert "Unaffected Canvas Area Preservation" in check_names
        assert "Alien Brand Intrusion Guard" in check_names
        assert "Old Incorrect Logo Eradication" in check_names
        assert "Official Brand Color Application" in check_names
        assert "Canonical Proportions & Distortion Check" in check_names

        for c in audit["checks"]:
            assert c["passed"] is True, f"Check failed: {c['name']} - {c['detail']}"

        # Verify Pepsi Blue (#004B93) was applied
        color_check = next(c for c in audit["checks"] if c["name"] == "Official Brand Color Application")
        assert "#004B93" in color_check["detail"]


def test_apple_card_preservation_and_no_false_margin_hazard():
    """
    Test Case 3: Apple card container framing.
    Assures that styled container cards do not trigger false safe margin hazards,
    and stretched logo is surgically replaced without canvas wiping.
    """
    img_bytes, filename, title, alt_text = synthesize_sample_preset_image("apple-certified-card")
    analysis = analyze_visual_asset(image_bytes=img_bytes, alt_text=alt_text)

    # Must detect Apple distorted logo
    assert analysis["detected_logo_name"] and analysis["detected_logo_name"].lower() == "apple"
    logo_issues = [iss for iss in analysis["visual_issues"] if "apple" in iss.get("title", "").lower() or iss.get("category") == "logo_integrity"]
    assert len(logo_issues) >= 1

    # Must NOT have false safe margin hazard for the container card frame
    margin_hazards = [iss for iss in analysis["visual_issues"] if iss.get("type") == "safe_margin_hazard"]
    assert len(margin_hazards) == 0

    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "orig_apple.png")
        corr_path = os.path.join(tmpdir, "corr_apple.png")

        with open(orig_path, "wb") as f:
            f.write(img_bytes)

        accepted_ids = [iss["id"] for iss in analysis["visual_issues"]]
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=accepted_ids,
            visual_issues=analysis["visual_issues"]
        )
        assert res["success"] is True

        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            visual_issues=analysis["visual_issues"],
            accepted_corrections=accepted_ids,
            brand_name="Apple"
        )
        assert audit["passed"] is True
        assert audit["status"] == "verified"


def test_lg_banner_preset_and_aspect_ratio_standardization():
    """
    Test Case 4: LG Display Banner preset.
    Assures irregular 2.79:1 ratio is detected and standardized to 16:9 non-destructively.
    """
    img_bytes, filename, title, alt_text = synthesize_sample_preset_image("lg-display-banner")
    analysis = analyze_visual_asset(image_bytes=img_bytes, alt_text=alt_text)

    assert analysis["image_width"] == 572
    assert analysis["image_height"] == 205
    assert analysis["aspect_ratio"] == "2.79:1"

    ratio_issues = [iss for iss in analysis["visual_issues"] if iss.get("type") == "non_standard_aspect_ratio"]
    assert len(ratio_issues) >= 1

    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "orig_lg.png")
        corr_path = os.path.join(tmpdir, "corr_lg.png")

        with open(orig_path, "wb") as f:
            f.write(img_bytes)

        accepted_ids = ["vis-layout-aspect-ratio"]
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=accepted_ids,
            visual_issues=analysis["visual_issues"]
        )
        assert res["success"] is True

        with Image.open(corr_path) as corr_img:
            corr_ratio = round(corr_img.width / corr_img.height, 2)
            # Standardized to 16:9 (1.78:1)
            assert 1.70 <= corr_ratio <= 1.85

        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            visual_issues=analysis["visual_issues"],
            accepted_corrections=accepted_ids,
            brand_name="LG"
        )
        assert audit["passed"] is True
        assert audit["status"] == "verified"


def test_enterprise_launch_poster_preset_findings():
    """
    Test Case 5: Enterprise Multi-Violation Launch Poster.
    Verifies casing error ('Linkedin'), copy typo ('unlimitted'), claim ('100% risk-free'),
    and disclaimer readability hazard.
    """
    img_bytes, filename, title, alt_text = synthesize_sample_preset_image("enterprise-launch-poster")
    analysis = analyze_visual_asset(image_bytes=img_bytes, alt_text=alt_text)

    issue_titles = [iss.get("title", "").lower() for iss in analysis["visual_issues"]]
    types = [iss.get("type", "") for iss in analysis["visual_issues"]]

    # Casing error
    assert any("linkedin" in t for t in issue_titles)
    # Typo
    assert any("unlimited" in t or "unlimitted" in t for t in issue_titles)
    # Absolute claim
    assert any("100% risk-free" in t or "absolute guarantee" in t for t in issue_titles)


def test_sample_presets_api_endpoints(db):
    """
    Test Case 6: Sample Presets API Endpoints.
    Verifies GET /multimodal/sample-presets and POST /multimodal/sample-presets/{preset_id}/load.
    """
    from scripts.seed_demo import seed_demo_environment
    from app.models.user import User
    from app.api.v1.endpoints.multimodal import (
        get_sample_presets,
        load_sample_preset_endpoint,
    )

    seed_demo_environment(db=db)
    creator = db.query(User).filter(User.email == "demo@contentguard.ai").first()
    assert creator is not None

    # 1. GET /sample-presets
    presets = get_sample_presets(current_user=creator)
    assert len(presets) == 4
    preset_ids = [p["id"] for p in presets]
    assert "pepsi-campaign-poster" in preset_ids

    # 2. POST /sample-presets/pepsi-campaign-poster/load
    res = load_sample_preset_endpoint(
        preset_id="pepsi-campaign-poster",
        current_user=creator,
        db=db
    )

    assert res["report_id"] is not None
    assert res["submission_id"] is not None
    assert res["preset_id"] == "pepsi-campaign-poster"
    assert "pepsi" in res["filename"].lower()
    assert len(res["visual_issues"]) >= 3
    assert res["wcag_compliance"] == "FAIL"
