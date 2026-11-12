import io
import pytest
from PIL import Image
from app.engine.multimodal_engine import (
    rgb_to_relative_luminance,
    calculate_contrast_ratio,
    extract_dominant_colors,
    evaluate_alt_text,
    analyze_visual_asset,
    color_distance_euclidean,
)
from app.models.brand_knowledge import BrandAsset


def test_wcag_luminance_and_contrast_ratio():
    """Verify WCAG 2.1 relative luminance and contrast calculations against standard benchmarks."""
    # Black and White must be 21:1
    white = (255, 255, 255)
    black = (0, 0, 0)
    assert calculate_contrast_ratio(white, black) == 21.0
    assert calculate_contrast_ratio(white, white) == 1.0

    # Relative luminance of pure white is 1.0, black is 0.0
    assert round(rgb_to_relative_luminance(255, 255, 255), 2) == 1.0
    assert round(rgb_to_relative_luminance(0, 0, 0), 2) == 0.0

    # Standard dark blue on white must pass AA (>4.5)
    dark_blue = (15, 23, 42)
    contrast = calculate_contrast_ratio(dark_blue, white)
    assert contrast > 10.0


def test_dominant_color_extraction():
    """Verify Pillow image processing extracts dominant colors and correct formats."""
    # Create a simple 100x100 red image with a blue rectangle
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    for x in range(20, 80):
        for y in range(20, 80):
            img.putpixel((x, y), (0, 0, 255))

    colors = extract_dominant_colors(img, max_colors=2)
    assert len(colors) >= 2
    hexes = [c["hex"] for c in colors]
    assert any(h == "#FF0000" for h in hexes)
    assert any(h == "#0000FF" for h in hexes)


def test_alt_text_evaluation():
    """Verify WCAG non-text content compliance auditing."""
    # Missing alt text
    res_missing = evaluate_alt_text(None)
    assert res_missing["verdict"] == "MISSING"
    assert res_missing["score"] == 0

    # Redundant "image of"
    res_redundant = evaluate_alt_text("Image of our executive leadership team at annual summit")
    assert any("image of" in iss.lower() for iss in res_redundant["issues"])
    assert res_redundant["score"] < 100

    # Concise valid alt text
    res_valid = evaluate_alt_text("Executive leadership team celebrating company anniversary at the annual summit.")
    assert res_valid["verdict"] == "EXCELLENT"
    assert res_valid["score"] >= 85


def test_full_multimodal_analysis_pipeline():
    """Verify end-to-end multimodal inspection on synthetic image buffer."""
    img = Image.new("RGB", (200, 100), color=(20, 30, 45))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    result = analyze_visual_asset(
        image_bytes=img_bytes,
        alt_text="Enterprise analytics dashboard showing operational metrics."
    )

    assert result["image_width"] == 200
    assert result["image_height"] == 100
    assert result["aspect_ratio"] == "2.0:1"
    assert "dominant_colors" in result
    assert "contrast_ratio" in result
    assert result["wcag_compliance"] in ["AAA_PASS", "AA_PASS", "FAIL"]
    assert result["alt_text_evaluation"]["verdict"] == "EXCELLENT"
    assert result["visual_score"] > 0
