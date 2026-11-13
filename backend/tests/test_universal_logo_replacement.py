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
