from typing import List, Dict, Any, Tuple
from app.models.analysis import ComplianceRating, IssueSeverity


SEVERITY_WEIGHTS = {
    IssueSeverity.CRITICAL.value: 25.0,
    IssueSeverity.HIGH.value: 15.0,
    IssueSeverity.MEDIUM.value: 7.0,
    IssueSeverity.LOW.value: 3.0,
}


def calculate_compliance_score(issues: List[Dict[str, Any]]) -> Tuple[float, str, Dict[str, int]]:
    """
    Calculates an explainable compliance score based on empirical findings and documented severity penalties:
    Base: 100
    Penalty = sum(weight_i)
    Score = max(0, 100 - Penalty)
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
