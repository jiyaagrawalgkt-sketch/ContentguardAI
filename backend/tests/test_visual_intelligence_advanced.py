import io
import pytest
from PIL import Image, ImageDraw, PngImagePlugin
from app.engine.multimodal_engine import (
    analyze_visual_asset,
    generate_corrected_visual_asset,
    VERIFIED_BRAND_REGISTRY,
    LogoMatchStatus,
    WCAGComplianceLevel,
)
from app.models.brand_knowledge import BrandAsset


def _create_test_canvas(
    width: int = 600,
    height: int = 600,
    bg_color: tuple = (255, 255, 255),
    png_text: str = None
) -> bytes:
    """Helper to generate a clean synthetic canvas with optional PNG text metadata."""
    img = Image.new("RGB", (width, height), color=bg_color)
    buf = io.BytesIO()
    
    if png_text:
        pnginfo = PngImagePlugin.PngInfo()
        pnginfo.add_text("description", png_text)
        img.save(buf, format="PNG", pnginfo=pnginfo)
    else:
        img.save(buf, format="PNG")
        
    return buf.getvalue()


# =========================================================================
# SCENARIO 1: Correct LinkedIn Logo (1:1 Canonical Square, Official #0A66C2)
# =========================================================================
def test_scenario_1_correct_linkedin_logo():
    """Verify official LinkedIn logo with canonical 1:1 ratio and official blue passes cleanly."""
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw LinkedIn Blue square in top-left zone (well away from border for clearspace)
    # x=40, y=40, w=60, h=60 (ratio 1.0:1, margin = 40/600 = 6.6% > 2.5%)
    draw.rectangle([40, 40, 100, 100], fill=(10, 102, 194))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Official LinkedIn Partner Summit presentation graphic."
    )
    
    assert result["detected_logo_name"] == "LinkedIn"
    assert result["logo_status"] == LogoMatchStatus.MATCHED.value
    # No distortion or color findings
    distortion_issues = [iss for iss in result["visual_issues"] if iss.get("type") == "logo_distortion"]
    color_issues = [iss for iss in result["visual_issues"] if iss.get("type") == "modified_logo_color"]
    assert len(distortion_issues) == 0
    assert len(color_issues) == 0


# =========================================================================
# SCENARIO 2: Modified LinkedIn Logo (Unofficial Purple Color)
# =========================================================================
def test_scenario_2_modified_linkedin_logo_color():
    """Verify unauthorized logo color modification is detected against official brand palette."""
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw square in top-left with purple color (unauthorized for LinkedIn)
    draw.rectangle([40, 40, 100, 100], fill=(160, 32, 240))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="LinkedIn official partner announcement."
    )
    
    assert result["detected_logo_name"] == "LinkedIn"
    color_issue = next((iss for iss in result["visual_issues"] if iss.get("type") == "modified_logo_color"), None)
    assert color_issue is not None
    assert color_issue["severity"] == "high"
    assert "#0A66C2" in color_issue["expected_reference"]
    assert color_issue["verification_status"] == "verified_official_reference"
    assert "Official LinkedIn Brand Guidelines" in color_issue["reference_source"]


# =========================================================================
# SCENARIO 3: Distorted Google Logo (Stretched 2.4:1 Proportions)
# =========================================================================
def test_scenario_3_distorted_google_logo():
    """Verify critical distortion detection when Google mark is stretched out of canonical ratio."""
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw horizontally stretched rectangle in top-left with Google Blue (66, 133, 244)
    # w=120, h=50 -> aspect ratio 2.4:1 vs canonical 1:1 (> 18% distortion)
    draw.rectangle([40, 40, 160, 90], fill=(66, 133, 244))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Google Cloud platform marketing creative."
    )
    
    assert result["detected_logo_name"] == "Google"
    assert result["logo_status"] == LogoMatchStatus.MISMATCHED.value
    
    dist_issue = next((iss for iss in result["visual_issues"] if iss.get("type") == "logo_distortion"), None)
    assert dist_issue is not None
    assert dist_issue["severity"] == "critical"
    assert "Google Brand Resource Center" in dist_issue["reference_source"]
    assert dist_issue["verification_status"] == "verified_official_reference"
    assert dist_issue["replacement_asset_url"] is not None


# =========================================================================
# SCENARIO 4: Poster with Absolute Commercial Claim
# =========================================================================
def test_scenario_4_absolute_promotional_claims():
    """Verify detection of unapproved absolute guarantees ('100% risk-free', '#1 in the world')."""
    raw_bytes = _create_test_canvas(
        width=600,
        height=600,
        png_text="PulseBuds Pro delivers #1 in the world sound fidelity with a 100% risk-free guarantee."
    )
    
    result = analyze_visual_asset(
        image_bytes=raw_bytes,
        alt_text="Product poster highlighting #1 in the world acoustic performance."
    )
    
    claim_issues = [iss for iss in result["visual_issues"] if iss.get("category") == "claims_promotional"]
    assert len(claim_issues) >= 1
    types = [iss["type"] for iss in claim_issues]
    assert "unsupported_absolute_claim" in types
    
    found_claim = claim_issues[0]
    assert found_claim["severity"] == "high"
    assert "Brand Legal" in found_claim["reference_source"]
    assert found_claim["correction_type"] == "text_correction"


# =========================================================================
# SCENARIO 5: Typography, Spelling & Microscopic Disclaimer
# =========================================================================
def test_scenario_5_typography_spelling_and_disclaimer():
    """Verify detection of trademark casing ('Linkedin'), typos ('revalutionary'), and sub-legible disclaimers."""
    img = Image.new("RGB", (600, 800), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Bottom zone microscopic text strip: y from 750 to 760 (h=10px -> 10/800 = 1.25% < 1.8%)
    draw.rectangle([40, 750, 400, 760], fill=(50, 50, 50))
    
    buf = io.BytesIO()
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("description", "Connect with us on Linkedin for revalutionary AI technology.")
    img.save(buf, format="PNG", pnginfo=pnginfo)
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Campaign poster for Linkedin audience."
    )
    
    issue_types = [iss["type"] for iss in result["visual_issues"]]
    assert "brand_name_casing_error" in issue_types
    assert "spelling_error" in issue_types
    assert "microscopic_disclaimer" in issue_types
    
    casing_issue = next(iss for iss in result["visual_issues"] if iss["type"] == "brand_name_casing_error")
    assert casing_issue["expected_reference"] == "Official Trademarked Brand Name: 'LinkedIn'"
    
    spelling_issue = next(iss for iss in result["visual_issues"] if iss["type"] == "spelling_error")
    assert spelling_issue["expected_reference"] == "Correct English spelling: 'revolutionary'"


# =========================================================================
# SCENARIO 6: Layout, Bleed Hazard & Non-Standard Aspect Ratio
# =========================================================================
def test_scenario_6_layout_bleed_and_aspect_ratio():
    """Verify safe margin bleed hazard (< 2% border distance) and non-standard advertising ratios."""
    # Create non-standard banner 1200x300 (4.0:1 aspect ratio)
    img = Image.new("RGB", (1200, 300), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw element dangerously touching border: x=5, y=5 (5/1200 = 0.4% margin < 2.0%)
    draw.rectangle([5, 5, 120, 60], fill=(20, 20, 20))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Web leader banner element."
    )
    
    issue_types = [iss["type"] for iss in result["visual_issues"]]
    assert "non_standard_aspect_ratio" in issue_types
    assert "safe_margin_hazard" in issue_types
    
    aspect_issue = next(iss for iss in result["visual_issues"] if iss["type"] == "non_standard_aspect_ratio")
    assert "4.0:1" in aspect_issue["detected_element"]


# =========================================================================
# SCENARIO 7: Multiple Simultaneous Violations in Single Pass
# =========================================================================
def test_scenario_7_multiple_simultaneous_violations():
    """Verify that multiple visual violations across all categories are captured in one pass."""
    # Poor contrast (light gray on white), distorted logo, absolute claim, and typo
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Stretched logo in top left with Google blue (w=120, h=50 -> 2.4:1 ratio departs from both 1:1 and 3.03:1)
    draw.rectangle([40, 40, 160, 90], fill=(66, 133, 244))
    # Low contrast element
    draw.rectangle([100, 250, 500, 400], fill=(245, 245, 245))
    
    buf = io.BytesIO()
    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("description", "Google Cloud guarantees 100% risk-free uptime with revalutionary speed.")
    img.save(buf, format="PNG", pnginfo=pnginfo)
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Cloud promo."
    )
    
    categories = {iss["category"] for iss in result["visual_issues"]}
    assert "logo_integrity" in categories
    assert "spelling_text" in categories
    assert "claims_promotional" in categories
    # Visual score must reflect multi-dimensional penalties
    assert result["visual_score"] < 70.0


# =========================================================================
# SCENARIO 8: Custom Organization Brand Asset in Knowledge Hub
# =========================================================================
def test_scenario_8_custom_organization_brand_asset():
    """Verify custom BrandAsset guidelines from organization Knowledge Hub are enforced."""
    custom_asset = BrandAsset(
        name="AlphaCore",
        asset_type="logo",
        primary_color_hex="#1E3A8A",
        rules_json={"canonical_aspect_ratio": 1.0, "min_clear_space_px": 24}
    )
    
    # Image with 2.2:1 distorted logo
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle([40, 40, 150, 90], fill=(30, 58, 138))  # #1E3A8A
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="AlphaCore internal corporate presentation.",
        brand_asset=custom_asset
    )
    
    org_issue = next((iss for iss in result["visual_issues"] if iss.get("type") == "logo_distortion"), None)
    assert org_issue is not None
    assert org_issue["verification_status"] == "verified_organization_asset"
    assert "Knowledge Hub: AlphaCore" in org_issue["reference_source"]


# =========================================================================
# SCENARIO 9: Unknown / Unregistered Brand Emblem
# =========================================================================
def test_scenario_9_unverified_unknown_brand():
    """Verify unknown emblem reports unverified status without inventing a fake standard."""
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # Draw an unverified square emblem in top_left
    draw.rectangle([40, 40, 100, 100], fill=(220, 20, 60))  # Crimson
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    
    result = analyze_visual_asset(
        image_bytes=buf.getvalue(),
        alt_text="Design asset for an unlisted third-party project."
    )
    
    unverified_issue = next((iss for iss in result["visual_issues"] if iss.get("type") == "unverified_brand_reference"), None)
    assert unverified_issue is not None
    assert unverified_issue["verification_status"] == "unverified_unknown_reference"
    assert "Unregistered Visual Identity" in unverified_issue["reference_source"]


# =========================================================================
# SCENARIO 10: Completely Compliant Poster & Meaningful Visual Correction
# =========================================================================
def test_scenario_10_compliant_poster_and_correction_generator(tmp_path):
    """Verify a compliant asset achieves high score and test meaningful correction generation."""
    # Compliant 1:1 canvas with LinkedIn logo, high contrast, clean alt text
    img = Image.new("RGB", (600, 600), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # LinkedIn Blue logo at safe position
    draw.rectangle([50, 50, 110, 110], fill=(10, 102, 194))
    # Dark content body for high contrast (luminance contrast > 10.0:1)
    draw.rectangle([50, 200, 550, 450], fill=(15, 23, 42))
    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()
    
    result = analyze_visual_asset(
        image_bytes=img_bytes,
        alt_text="Official LinkedIn Talent Solutions annual conference presentation banner."
    )
    
    assert result["visual_score"] >= 90.0
    critical_or_high = [iss for iss in result["visual_issues"] if iss.get("severity") in ["critical", "high"]]
    assert len(critical_or_high) == 0
    assert result["wcag_compliance"] in [WCAGComplianceLevel.AAA_PASS.value, WCAGComplianceLevel.AA_PASS.value]
    
    # Test Visual Correction Generator
    input_file = tmp_path / "original.png"
    output_file = tmp_path / "corrected.png"
    with open(input_file, "wb") as f:
        f.write(img_bytes)
        
    correction_res = generate_corrected_visual_asset(
        original_image_path=str(input_file),
        output_path=str(output_file),
        accepted_corrections=["contrast_enhancement", "logo_replacement", "spacing_adjustment"]
    )
    
    assert output_file.exists()
    corrected_img = Image.open(str(output_file))
    assert corrected_img.width == 600
    assert corrected_img.height == 600
    assert correction_res["format"] == "PNG"
