import re
from typing import List, Dict, Any, Tuple, Optional
from app.models.analysis import ComplianceRating, IssueSeverity


SEVERITY_WEIGHTS = {
    IssueSeverity.CRITICAL.value: 25.0,
    IssueSeverity.HIGH.value: 15.0,
    IssueSeverity.MEDIUM.value: 7.0,
    IssueSeverity.LOW.value: 3.0,
}


def calculate_compliance_score(issues: List[Dict[str, Any]]) -> Tuple[float, str, Dict[str, int]]:
    """
    Backward-compatible compliance score calculation based on issues list.
    """
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
    }

    total_penalty = 0.0

    for issue in issues:
        sev = str(issue.get("severity", "low")).lower()
        if sev in counts:
            counts[sev] += 1
            total_penalty += SEVERITY_WEIGHTS.get(sev, 3.0)
        else:
            counts["low"] += 1
            total_penalty += 3.0

    score = max(0.0, round(100.0 - total_penalty, 1))

    if score >= 90.0:
        rating = ComplianceRating.COMPLIANT.value
    elif score >= 75.0:
        rating = ComplianceRating.NEEDS_REVIEW.value
    elif score >= 50.0:
        rating = ComplianceRating.HIGH_RISK.value
    else:
        rating = ComplianceRating.CRITICAL_VIOLATIONS.value

    return score, rating, counts


def calculate_content_quality_score(content: str) -> Tuple[float, List[Dict[str, Any]]]:
    """
    Calculates readability and clarity score based on sentence length, word count, and repetition.
    """
    if not content or not content.strip():
        return 0.0, [{"metric": "Content Empty", "penalty": 100.0, "reason": "No content provided."}]

    deductions = []
    penalty = 0.0

    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if s.strip()]
    words = re.findall(r"\b\w+\b", content)

    # 1. Average sentence length check
    if sentences:
        avg_words = len(words) / max(1, len(sentences))
        if avg_words > 30:
            ded = 15.0
            penalty += ded
            deductions.append({
                "metric": "Sentence Length",
                "penalty": ded,
                "reason": f"Average sentence length is {avg_words:.1f} words (recommended: under 25 words)."
            })
        elif avg_words > 25:
            ded = 8.0
            penalty += ded
            deductions.append({
                "metric": "Sentence Length",
                "penalty": ded,
                "reason": f"Average sentence length is {avg_words:.1f} words (recommended: under 25 words)."
            })

    # 2. Extremely long sentence detection
    long_sentences = [s for s in sentences if len(s.split()) > 35]
    if long_sentences:
        ded = min(15.0, len(long_sentences) * 5.0)
        penalty += ded
        deductions.append({
            "metric": "Complex Sentences",
            "penalty": ded,
            "reason": f"{len(long_sentences)} sentence(s) exceed 35 words and impair readability."
        })

    # 3. Excessive repetition check
    word_freq: Dict[str, int] = {}
    for w in words:
        wl = w.lower()
        if len(wl) > 5:
            word_freq[wl] = word_freq.get(wl, 0) + 1
    
    repeated = [w for w, c in word_freq.items() if c >= 4 and len(words) < 100]
    if repeated:
        ded = min(10.0, len(repeated) * 3.0)
        penalty += ded
        deductions.append({
            "metric": "Vocabulary Repetition",
            "penalty": ded,
            "reason": f"Repeated terms detected: {', '.join(repeated[:3])}."
        })

    quality_score = max(0.0, round(100.0 - penalty, 1))
    return quality_score, deductions


def calculate_comprehensive_scores(
    brand_issues: List[Dict[str, Any]],
    verified_claims: Optional[List[Dict[str, Any]]] = None,
    content_text: Optional[str] = None
) -> Dict[str, Any]:
    """
    Transparent, multi-dimensional scoring pipeline separating:
    A. Brand Compliance Score (Voice, restricted terms, guidelines)
    B. Evidence Confidence Score (Supported, unsupported, conflicting, outdated claims)
    C. Content Quality Score (Readability, sentence structure, repetition)
    D. Overall Publication Risk (Composite readiness)

    Ensures that a 100/100 score is ONLY possible when ALL factual claims are verified and compliant!
    """
    # 1. Brand Compliance Score
    brand_score, brand_rating, counts = calculate_compliance_score(brand_issues)
    brand_deductions = [
        {
            "issue": iss.get("issue_type") or iss.get("matched_text"),
            "severity": iss.get("severity", "medium"),
            "penalty": SEVERITY_WEIGHTS.get(str(iss.get("severity", "low")).lower(), 3.0),
            "reason": iss.get("explanation") or "Brand guideline violation"
        }
        for iss in brand_issues
    ]

    # 2. Evidence Confidence Score
    claims = verified_claims or []
    evidence_penalty = 0.0
    evidence_deductions = []

    for c in claims:
        status_val = str(c.get("verification_status", "unverified")).lower()
        claim_label = c.get("claim_text") or "Factual assertion"

        if status_val == "supported":
            pass # Zero penalty
        elif status_val == "conflicting":
            pen = 30.0
            evidence_penalty += pen
            evidence_deductions.append({
                "claim": claim_label,
                "status": "conflicting",
                "penalty": pen,
                "reason": c.get("explanation") or "Asserted claim directly contradicts official approved knowledge."
            })
        elif status_val == "outdated":
            pen = 20.0
            evidence_penalty += pen
            evidence_deductions.append({
                "claim": claim_label,
                "status": "outdated",
                "penalty": pen,
                "reason": c.get("explanation") or "Supporting document or fact has expired validity date."
            })
        elif status_val in ["unsupported", "unverified"]:
            pen = 18.0
            evidence_penalty += pen
            evidence_deductions.append({
                "claim": claim_label,
                "status": "unsupported",
                "penalty": pen,
                "reason": c.get("explanation") or "No approved evidence or whitepaper corroborates this claim in the Knowledge Hub."
            })

    evidence_score = max(0.0, round(100.0 - evidence_penalty, 1))

    # 3. Content Quality Score
    quality_score, quality_deductions = calculate_content_quality_score(content_text or "")

    # 4. Composite Overall Score
    # If factual claims exist: 50% Brand + 40% Evidence + 10% Quality
    # If no factual claims: 85% Brand + 15% Quality
    if claims:
        overall_score = round(
            0.50 * brand_score + 0.40 * evidence_score + 0.10 * quality_score,
            1
        )
    else:
        overall_score = round(
            0.85 * brand_score + 0.15 * quality_score,
            1
        )

    # Hard ceiling caps:
    # If any Critical brand violation exists or Conflicting evidence exists, cap overall at 60
    has_critical = counts.get("critical", 0) > 0 or any(c.get("verification_status") == "conflicting" for c in claims)
    if has_critical and overall_score > 60.0:
        overall_score = 60.0

    # If any Unsupported claims exist, overall score cannot exceed 85.0 (Cannot get 100!)
    has_unsupported = any(c.get("verification_status") in ["unsupported", "outdated"] for c in claims)
    if has_unsupported and overall_score > 85.0:
        overall_score = 85.0

    # Rating
    if overall_score >= 90.0:
        overall_rating = ComplianceRating.COMPLIANT.value
        publication_risk = "low"
    elif overall_score >= 75.0:
        overall_rating = ComplianceRating.NEEDS_REVIEW.value
        publication_risk = "medium"
    elif overall_score >= 50.0:
        overall_rating = ComplianceRating.HIGH_RISK.value
        publication_risk = "high"
    else:
        overall_rating = ComplianceRating.CRITICAL_VIOLATIONS.value
        publication_risk = "critical"

    return {
        "overall_score": overall_score,
        "compliance_rating": overall_rating,
        "publication_risk": publication_risk,
        "brand_compliance_score": brand_score,
        "evidence_confidence_score": evidence_score,
        "content_quality_score": quality_score,
        "counts": counts,
        "breakdown": {
            "brand_deductions": brand_deductions,
            "evidence_deductions": evidence_deductions,
            "quality_deductions": quality_deductions,
            "formula": "50% Brand Compliance + 40% Evidence Confidence + 10% Content Quality" if claims else "85% Brand Compliance + 15% Content Quality",
        }
    }
