"""
Universal Brand Logo Recognition, Official Reference Replacement & Post-Correction Verification Test Suite

Covers all 10 user-specified enterprise testing scenarios:
1. Scenario 1: Red LinkedIn logo detected as modified_logo_color (#FC0104 vs #0A66C2).
2. Scenario 2: Apply Fix generates replacement with official LinkedIn Blue (#0A66C2) 1:1 vector mark.
3. Scenario 3: Post-correction verification independently audits corrected image: 0 residual red pixels, passed: True.
4. Scenario 4: Distorted Google logo corrected to canonical 1:1 'G' mark.
5. Scenario 5: Incorrect Microsoft logo detected and replaced with official 4-color square tiles.
6. Scenario 6: Incorrect wordmark identified and replaced.
7. Scenario 7: Correct official logo not unnecessarily modified (score >= 90).
8. Scenario 8: Approved monochrome variant (e.g. white Apple on black) not flagged as off-brand.
9. Scenario 9: Custom company logo verified using registered BrandAsset in DB.
10. Scenario 10: Unknown brands reported as unverified_unknown_reference without fabricated verification.
"""

import io
import os
import tempfile
import pytest
from PIL import Image, ImageDraw

from app.engine.multimodal_engine import (
    analyze_visual_asset,
    generate_corrected_visual_asset,
    verify_corrected_visual_asset,
    render_official_brand_asset,
    detect_visual_elements_and_regions,
    VERIFIED_BRAND_REGISTRY,
    LogoMatchStatus,
)
from app.models.brand_knowledge import BrandAsset
from app.models.organization import Organization


# =========================================================================
# SCENARIO 1: Red LinkedIn Logo Detection (Color Modification Detected)
# =========================================================================
def test_scenario_1_red_linkedin_logo_detected_as_modified_color():
    """Uploaded image containing a red LinkedIn logo is identified and flagged as modified_logo_color."""
    # Create white canvas with a large red LinkedIn logo (aspect ratio 1.0:1)
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw red logo box
    draw.rounded_rectangle([50, 50, 550, 550], radius=40, fill=(252, 1, 4))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="LinkedIn brand banner"
    )
    
    assert result["detected_logo_name"] == "LinkedIn"
    color_issues = [iss for iss in result["visual_issues"] if iss.get("type") == "modified_logo_color"]
    assert len(color_issues) >= 1
    
    issue = color_issues[0]
    assert issue["category"] == "logo_integrity"
    assert "FC0104" in issue["detected_element"].upper() or "RED" in issue["detected_element"].upper()
    assert "0A66C2" in issue["expected_reference"].upper()
    assert issue["verification_status"] == "verified_official_reference"
    assert "brand_key" in issue and issue["brand_key"] == "linkedin"
    assert "available_variants" in issue and "primary" in issue["available_variants"]


# =========================================================================
# SCENARIO 2: Apply Fix Generates Replacement With Official LinkedIn Blue
# =========================================================================
def test_scenario_2_apply_fix_replaces_red_logo_with_official_blue():
    """Apply Fix erases the red logo completely and composites the official LinkedIn mark."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "red_linkedin.png")
        corr_path = os.path.join(tmpdir, "corrected_linkedin.png")
        
        # Create synthetic red LinkedIn logo image
        img = Image.new("RGB", (600, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([50, 50, 550, 550], radius=40, fill=(252, 1, 4))
        img.save(orig_path, format="PNG")
        
        # Analyze first to get visual issues
        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="LinkedIn logo graphic")
        
        # Run replacement
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["contrast_enhancement"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="primary"
        )
        
        assert os.path.exists(corr_path)
        assert res["success"] is True
        
        # Inspect pixel data of corrected image
        corr_img = Image.open(corr_path).convert("RGB")
        w, h = corr_img.size
        
        red_count = 0
        blue_count = 0
        for y in range(h):
            for x in range(w):
                r, g, b = corr_img.getpixel((x, y))
                # Red pixel check (#FC0104: r > 180 and g < 60 and b < 60)
                if r > 180 and g < 60 and b < 60:
                    red_count += 1
                # Official LinkedIn Blue check (#0A66C2: r < 40 and g > 70 and b > 160)
                if r < 40 and g > 70 and b > 160:
                    blue_count += 1
                    
        # Red pixels must be 0 (100% erased)
        assert red_count == 0, f"Expected 0 residual red pixels, found {red_count}"
        # Official blue pixels must be prominent
        assert blue_count > 10000, f"Expected official blue pixels, found {blue_count}"


# =========================================================================
# SCENARIO 3: Post-Correction Verification Independently Passes
# =========================================================================
def test_scenario_3_independent_post_correction_verification_passes():
    """Independent post-correction audit verifies 0 residual bad pixels, official color, and passed: True."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "red_input.png")
        corr_path = os.path.join(tmpdir, "corrected_out.png")
        
        # Synthetic red input
        img = Image.new("RGB", (600, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rounded_rectangle([40, 40, 560, 560], radius=40, fill=(252, 1, 4))
        img.save(orig_path, format="PNG")
        
        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="LinkedIn logo graphic")
            
        generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["contrast_enhancement"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="primary"
        )
        
        audit_res = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="LinkedIn",
            visual_issues=analysis["visual_issues"],
            brand_asset=None,
            selected_variant="primary"
        )
        
        assert audit_res["passed"] is True
        assert audit_res["status"] == "verified"
        assert audit_res["residual_offending_pixels"] == 0
        assert audit_res["residual_bad_pixel_pct"] == 0.0
        assert audit_res["canonical_color_pct"] >= 8.0
        
        # All individual checks must pass
        for chk in audit_res["checks"]:
            assert chk["passed"] is True, f"Check '{chk['name']}' failed: {chk['detail']}"


# =========================================================================
# SCENARIO 4: Distorted Google Logo Corrected to Canonical 1:1 'G' Mark
# =========================================================================
def test_scenario_4_distorted_google_logo_corrected():
    """Stretched/distorted Google logo is identified and replaced with canonical 1:1 vector mark."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "google_distorted.png")
        corr_path = os.path.join(tmpdir, "google_corrected.png")
        
        # Create heavily stretched Google-colored banner (ratio 2.5:1)
        img = Image.new("RGB", (750, 300), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 30, 700, 270], fill=(66, 133, 244))  # Google Blue rectangle stretched
        img.save(orig_path, format="PNG")
        
        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="Google official partner summit")
            
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["contrast_enhancement"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="primary"
        )
        
        assert res["success"] is True
        assert os.path.exists(corr_path)
        
        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="Google",
            visual_issues=analysis["visual_issues"],
            brand_asset=None,
            selected_variant="primary"
        )
        assert audit["passed"] is True
        assert audit["canonical_color_pct"] >= 5.0


# =========================================================================
# SCENARIO 5: Incorrect Microsoft Logo Replaced With 4-Color Square Tiles
# =========================================================================
def test_scenario_5_microsoft_logo_replacement():
    """Incorrect Microsoft logo replaced with official 4-color square grid."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "ms_wrong.png")
        corr_path = os.path.join(tmpdir, "ms_corrected.png")
        
        # Wrong monochrome purple Microsoft mark
        img = Image.new("RGB", (600, 600), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([100, 100, 500, 500], fill=(128, 0, 128))
        img.save(orig_path, format="PNG")
        
        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="Microsoft Azure cloud platform")
            
        generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["contrast_enhancement"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="primary"
        )
        
        # Check that corrected image contains Microsoft 4 brand colors:
        # Red-Orange #F25022, Green #7FBA00, Blue #00A4EF, Yellow #FFB900
        corr_img = Image.open(corr_path).convert("RGB")
        w, h = corr_img.size
        found_ms_blue = False
        found_ms_green = False
        for y in range(h):
            for x in range(w):
                r, g, b = corr_img.getpixel((x, y))
                # MS Blue #00A4EF (r < 20, g > 140, b > 210)
                if r < 20 and g > 140 and b > 210:
                    found_ms_blue = True
                # MS Green #7FBA00 (r in 110..140, g in 170..200, b < 20)
                if 100 < r < 150 and 160 < g < 210 and b < 20:
                    found_ms_green = True
                    
        assert found_ms_blue is True, "Microsoft official blue tile missing in replacement"
        assert found_ms_green is True, "Microsoft official green tile missing in replacement"


# =========================================================================
# SCENARIO 6: Wordmark Replacement
# =========================================================================
def test_scenario_6_wordmark_replacement():
    """Generating corrected visual with 'wordmark' variant produces valid official asset."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "wordmark_input.png")
        corr_path = os.path.join(tmpdir, "wordmark_out.png")
        
        img = Image.new("RGB", (700, 350), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.rectangle([50, 50, 650, 300], fill=(200, 20, 20))
        img.save(orig_path, format="PNG")
        
        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="Amazon AWS enterprise services")
            
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["contrast_enhancement"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="wordmark"
        )
        assert res["success"] is True
        assert os.path.exists(corr_path)


# =========================================================================
# SCENARIO 7: Correct Official Logo Not Unnecessarily Modified
# =========================================================================
def test_scenario_7_correct_official_logo_passes_with_high_score():
    """A graphic featuring official LinkedIn Blue 1:1 mark with proper clearspace gets visual score >= 90 and 0 logo violations."""
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Canonical 1:1 LinkedIn Blue mark centered with safe 10% margins
    draw.rounded_rectangle([60, 60, 540, 540], radius=35, fill=(10, 102, 194))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Official LinkedIn presentation graphic"
    )
    
    assert result["detected_logo_name"] == "LinkedIn"
    assert result["logo_status"] == LogoMatchStatus.MATCHED.value
    assert result["visual_score"] >= 90
    
    logo_issues = [iss for iss in result["visual_issues"] if iss.get("category") == "logo_integrity"]
    assert len(logo_issues) == 0, f"Expected 0 logo violations, found: {logo_issues}"


# =========================================================================
# SCENARIO 8: Approved Monochrome Variant Not Flagged as Off-Brand
# =========================================================================
def test_scenario_8_approved_monochrome_variant_not_flagged():
    """White monochrome Apple logo on dark background is recognized as approved variant without color violation."""
    img = Image.new("RGB", (600, 600), color=(18, 18, 20))  # Dark canvas
    draw = ImageDraw.Draw(img)
    # Crisp white square representing white monochrome Apple mark
    draw.rounded_rectangle([150, 150, 450, 450], radius=30, fill=(255, 255, 255))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Apple developer conference banner"
    )
    
    assert result["detected_logo_name"] == "Apple"
    # Must NOT flag modified_logo_color because monochrome_white is an approved official variant
    color_issues = [iss for iss in result["visual_issues"] if iss.get("type") == "modified_logo_color"]
    assert len(color_issues) == 0, f"Monochrome white falsely flagged as color issue: {color_issues}"


# =========================================================================
# SCENARIO 9: Custom Company Logo Verified Using Registered BrandAsset
# =========================================================================
def test_scenario_9_custom_organization_brand_asset(db):
    """Custom organization logo registered in database is recognized as verified_organization_asset."""
    # Register organization first to satisfy foreign key constraint
    org = Organization(
        id="org_test_enterprise",
        name="Acme Enterprise",
        slug="acme-enterprise"
    )
    db.add(org)
    db.commit()

    # Register custom brand asset in DB
    asset = BrandAsset(
        organization_id="org_test_enterprise",
        name="Acme Corp Primary Emblem",
        asset_type="logo",
        file_path="uploads/brands/acme_emblem.png",
        primary_color_hex="#FF5722",
        rules_json={"canonical_aspect_ratio": 1.0, "min_clear_space_px": 20},
        is_active=True
    )
    db.add(asset)
    db.commit()
    
    # Render synthetic canvas with Acme deep orange
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([60, 60, 540, 540], radius=30, fill=(255, 87, 34))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Acme Corp enterprise security solution",
        brand_asset=asset
    )
    
    assert result["detected_logo_name"] == "Acme Corp Primary Emblem"
    assert result["logo_status"] == LogoMatchStatus.MATCHED.value
    # Visual score should be compliant
    assert result["visual_score"] >= 70


# =========================================================================
# SCENARIO 10: Unknown Brands Reported as Unverified Unknown Reference
# =========================================================================
def test_scenario_10_unknown_brands_not_fabricated():
    """Unregistered / unrecognized brand graphics are flagged as unverified without fake verification."""
    # Create canvas with random off-brand colors and arbitrary text
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 560, 560], fill=(73, 19, 142))  # Arbitrary purple
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Unknown startup banner without brand metadata"
    )
    
    # Must NOT report LinkedIn, Google, or any known brand
    assert result["detected_logo_name"] in [None, "Unknown Logo", "Custom Brand Logo"]
    # If any finding is logged, verification_status must NOT be verified_official_reference
    for iss in result["visual_issues"]:
        if iss.get("category") == "logo_integrity":
            assert iss.get("verification_status") != "verified_official_reference"


# =========================================================================
# SCENARIO 11: LG Banner Aspect Ratio Standardization (2.79:1 -> 16:9)
# =========================================================================
def test_scenario_11_lg_banner_aspect_ratio_standardization_non_destructive():
    """
    LG company logo banner (572x205px, 2.79:1 aspect ratio) standardizes canvas to 16:9
    with seamless letterboxing, leaving the original LG graphic 100% intact,
    and never replacing with an alien blue box.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "lg_banner.png")
        corr_path = os.path.join(tmpdir, "lg_corrected.png")

        # Create synthetic LG banner: 572x205px with dark top/bottom bars, white center band, and LG mark
        w, h = 572, 205
        img = Image.new("RGB", (w, h), color=(20, 20, 20))
        draw = ImageDraw.Draw(img)
        # White center band
        draw.rectangle([0, 35, w, 170], fill=(255, 255, 255))
        # LG Red emblem circle
        draw.ellipse([80, 50, 160, 130], fill=(196, 18, 48))
        # Wordmark "LG" in grey
        draw.rectangle([180, 60, 195, 120], fill=(107, 109, 111))
        draw.rectangle([180, 110, 215, 120], fill=(107, 109, 111))
        img.save(orig_path, format="PNG")

        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="LG electronics corporate banner")

        # Confirm non-standard aspect ratio is detected
        ratio_issues = [iss for iss in analysis["visual_issues"] if "aspect" in iss.get("type", "")]
        assert len(ratio_issues) >= 1
        assert "2.79:1" in ratio_issues[0]["title"] or "2.79:1" in ratio_issues[0]["detected_element"]

        # Apply fix ONLY for aspect ratio
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["vis-layout-aspect-ratio"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"]
        )

        assert res["success"] is True
        assert os.path.exists(corr_path)

        corr_img = Image.open(corr_path)
        cw, ch = corr_img.size
        new_ratio = cw / ch
        # Must be standard 16:9 landscape format (approx 1.778:1)
        assert 1.70 <= new_ratio <= 1.85
        assert cw == 572
        assert ch == 321 or ch == 322

        # Verify NO LinkedIn Blue (#0A66C2) was injected
        corr_pixels = list(corr_img.getdata())
        linkedin_blue = (10, 102, 194)
        alien_pixels = sum(
            1 for p in corr_pixels
            if (abs(p[0] - linkedin_blue[0]) + abs(p[1] - linkedin_blue[1]) + abs(p[2] - linkedin_blue[2])) < 40
        )
        assert alien_pixels == 0, "No alien LinkedIn Blue box should be injected into LG banner!"

        # Independent verification check
        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="LG",
            visual_issues=analysis["visual_issues"],
            accepted_corrections=["vis-layout-aspect-ratio"]
        )
        assert audit["passed"] is True
        assert audit["status"] == "verified"


# =========================================================================
# SCENARIO 12: Apple Logo in Card Corrected Without Canvas Wiping
# =========================================================================
def test_scenario_12_apple_logo_in_card_corrected_without_canvas_wiping():
    """
    Apple logo inside a white rounded card on a blue outer background:
    Distorted logo is surgically corrected inside the card, while the outer blue frame
    and white card remain 100% intact (no whole-canvas wiping).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "apple_card.png")
        corr_path = os.path.join(tmpdir, "apple_corrected.png")

        # 331x319px canvas with outer dark blue border, white card, and distorted Apple mark
        w, h = 331, 319
        img = Image.new("RGB", (w, h), color=(16, 36, 48))
        draw = ImageDraw.Draw(img)
        # White rounded card
        draw.rounded_rectangle([18, 18, 313, 301], radius=24, fill=(251, 251, 251))
        # Stretched Apple mark (aspect ratio 1.04:1)
        draw.ellipse([90, 75, 240, 220], fill=(0, 0, 0))
        img.save(orig_path, format="PNG")

        with open(orig_path, "rb") as f:
            analysis = analyze_visual_asset(f.read(), alt_text="Apple certified device accessory")

        # Apply logo distortion correction
        res = generate_corrected_visual_asset(
            original_image_path=orig_path,
            output_path=corr_path,
            accepted_corrections=["vis-logo-distortion-apple"],
            brand_asset=None,
            visual_issues=analysis["visual_issues"],
            selected_variant="primary"
        )

        assert res["success"] is True
        assert os.path.exists(corr_path)

        corr_img = Image.open(corr_path)
        assert corr_img.size == (331, 319)

        # Inspect unaffected card background: white card interior must STILL BE WHITE, not wiped to solid blue!
        card_interior_pixel = corr_img.getpixel((50, 50))
        assert card_interior_pixel[0] > 240 and card_interior_pixel[1] > 240 and card_interior_pixel[2] > 240, (
            f"White card interior was wiped out! Expected near white, got {card_interior_pixel}"
        )

        # Inspect outer frame: must STILL BE DARK BLUE
        outer_frame_pixel = corr_img.getpixel((5, 5))
        assert outer_frame_pixel[0] < 30 and outer_frame_pixel[1] < 50, (
            f"Outer frame was altered! Got {outer_frame_pixel}"
        )

        # Independent verification check
        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="Apple",
            visual_issues=analysis["visual_issues"],
            accepted_corrections=["vis-logo-distortion-apple"]
        )
        assert audit["passed"] is True
        assert audit["status"] == "verified"


# =========================================================================
# SCENARIO 13: Alien Brand Intrusion Guard Blocks Foreign Brand Injection
# =========================================================================
def test_scenario_13_alien_brand_intrusion_guard_fails_on_foreign_color():
    """Verification independently detects foreign brand injection (e.g. LinkedIn Blue in an LG visual) and FAILS."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "lg_orig.png")
        corr_path = os.path.join(tmpdir, "lg_bad_alien.png")

        # Original LG image
        img = Image.new("RGB", (400, 400), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.ellipse([50, 50, 350, 350], fill=(196, 18, 48))
        img.save(orig_path, format="PNG")

        # Contaminated corrected image with an alien LinkedIn blue square injected
        corr_img = Image.new("RGB", (400, 400), color=(255, 255, 255))
        corr_draw = ImageDraw.Draw(corr_img)
        corr_draw.rounded_rectangle([100, 100, 300, 300], radius=20, fill=(10, 102, 194))  # LinkedIn Blue injected!
        corr_img.save(corr_path, format="PNG")

        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="LG",
            visual_issues=[{"id": "vis-logo-distortion-lg", "category": "logo_integrity", "brand_key": "lg"}]
        )

        # Must FAIL due to alien brand intrusion!
        assert audit["passed"] is False
        assert audit["status"] == "failed"
        alien_checks = [c for c in audit["checks"] if "Alien Brand Intrusion Guard" in c["name"]]
        assert len(alien_checks) >= 1
        assert alien_checks[0]["passed"] is False


# =========================================================================
# SCENARIO 14: Non-Destructive Verification Catches Damaged Canvas Elements
# =========================================================================
def test_scenario_14_damaged_canvas_fails_preservation_audit():
    """Verification FAILS if unrelated background or artwork was wiped out during correction."""
    with tempfile.TemporaryDirectory() as tmpdir:
        orig_path = os.path.join(tmpdir, "art_orig.png")
        corr_path = os.path.join(tmpdir, "art_wiped.png")

        # Complex artwork with patterned background
        img = Image.new("RGB", (500, 500), color=(255, 240, 200))
        draw = ImageDraw.Draw(img)
        # Background elements
        draw.rectangle([20, 20, 480, 150], fill=(30, 60, 90))
        draw.rectangle([20, 350, 480, 480], fill=(90, 30, 60))
        # Logo in center
        draw.ellipse([200, 200, 300, 300], fill=(0, 0, 0))
        img.save(orig_path, format="PNG")

        # Flawed correction engine wiped the whole canvas to solid black
        corr_img = Image.new("RGB", (500, 500), color=(0, 0, 0))
        corr_img.save(corr_path, format="PNG")

        audit = verify_corrected_visual_asset(
            original_image_path=orig_path,
            corrected_image_path=corr_path,
            brand_name="Apple",
            visual_issues=[{
                "id": "vis-logo-apple",
                "category": "logo_integrity",
                "brand_key": "apple",
                "region": {"x": 40.0, "y": 40.0, "width": 20.0, "height": 20.0}
            }]
        )

        assert audit["passed"] is False
        preservation_checks = [c for c in audit["checks"] if "Unaffected Canvas Area Preservation" in c["name"]]
        assert len(preservation_checks) >= 1
        assert preservation_checks[0]["passed"] is False

