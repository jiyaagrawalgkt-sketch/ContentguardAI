import re
import json
import logging
from typing import List, Dict, Any, Tuple, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.brand_knowledge import BrandGuideline, ApprovedFact
from app.engine.deterministic import run_deterministic_analysis
from app.engine.scoring import calculate_compliance_score
from app.engine.correction_engine import determine_correction_strategy

logger = logging.getLogger(__name__)


def redact_secrets_for_ai(text: str) -> str:
    """
    CRITICAL AI SAFETY FILTER:
    Redacts detected passwords, API keys, private tokens, and credentials
    BEFORE sending any content to an external AI provider (Gemini).
    """
    if not text:
        return text

    # Redact AWS Access Keys
    redacted = re.sub(r"\bAKIA[0-9A-Z]{16}\b", "[REDACTED_AWS_KEY]", text)
    # Redact GitHub Tokens
    redacted = re.sub(r"\bghp_[a-zA-Z0-9]{36}\b", "[REDACTED_GITHUB_TOKEN]", redacted)
    # Redact Slack Tokens
    redacted = re.sub(r"\bxox[baprs]-[a-zA-Z0-9-]{10,48}\b", "[REDACTED_SLACK_TOKEN]", redacted)
    # Redact Private Keys
    redacted = re.sub(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY[^\n-]*-----[\s\S]*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", "[REDACTED_PRIVATE_KEY]", redacted)
    # Redact Database URIs
    redacted = re.sub(r"\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|sqlite):\/\/[^\s\"'<>]+", "[REDACTED_DATABASE_URI]", redacted)
    # Redact Plaintext Secret Assignments
    redacted = re.sub(r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|password|passwd|pwd)\s*[:=]\s*['\"][^'\"]+['\"]", "[REDACTED_CREDENTIAL]", redacted)
    return redacted


def analyze_content(
    content: str,
    organization_id: str,
    db: Session,
    category: Optional[str] = None,
    target_platform: Optional[str] = None,
) -> Tuple[List[Dict[str, Any]], float, str, Dict[str, int], str]:
    """
    Comprehensive Hybrid Content Compliance & Data-Loss Prevention Pipeline:
    1. Layer 1: Multi-category deterministic rule engine (runs locally, zero network dependence).
    2. Layer 2: If Gemini API key is configured, securely executes contextual AI analysis
       with all credentials redacted before transmission.
    3. Layer 3: Merges findings, deduplicates overlapping spans, maintains provenance,
       and calculates explainable mathematical compliance score.
    Returns: (issues, compliance_score, compliance_rating, counts, engine_mode)
    """
    # -----------------------------------------------------------------
    # Layer 1: Deterministic Baseline Analysis
    # -----------------------------------------------------------------
    logger.info(f"Executing Layer 1 deterministic analysis for org {organization_id} (draft length: {len(content)} chars)")
    issues = run_deterministic_analysis(
        content=content,
        organization_id=organization_id,
        db=db,
        category=category,
        target_platform=target_platform
    )
    logger.info(f"Layer 1 finished: {len(issues)} deterministic violation(s) identified.")
    engine_mode = "deterministic_fallback"

    # -----------------------------------------------------------------
    # Layer 2: Secure Contextual Gemini Enrichment (if configured)
    # -----------------------------------------------------------------
    if settings.GEMINI_API_KEY and len(settings.GEMINI_API_KEY.strip()) > 5:
        try:
            logger.info("Gemini API key detected. Initiating Layer 2 AI Contextual analysis...")
            from google import genai
            from google.genai import types

            # Fetch organization guidelines to ground prompt
            guidelines = db.query(BrandGuideline).filter(
                BrandGuideline.organization_id == organization_id,
                BrandGuideline.is_active == True
            ).all()

            guidelines_context = "\n".join([
                f"- [{g.category.upper()}] {g.title}: {g.description}"
                for g in guidelines
            ])

            # REDACT SENSITIVE CREDENTIALS BEFORE TRANSMITTING TO LLM
            sanitized_content = redact_secrets_for_ai(content)

            client = genai.Client(api_key=settings.GEMINI_API_KEY)
            prompt = f"""You are ContentGuard AI's enterprise brand governance, privacy, and compliance engine.
Analyze the following marketing/business copy for risks across ALL six categories:

1. CONFIDENTIAL INFORMATION & DATA LEAKAGE:
   - Unannounced client names, private enterprise relationships (e.g., 'confidential Tier-1 banking clients in New York')
   - Internal project codenames, unreleased product features, internal roadmaps
   - Non-public financial figures, burn rates, margins, EBITDA, private deal terms
2. PERSONAL INFORMATION & PRIVACY RISKS (PII):
   - Personal emails, phone numbers, private residential locations, government IDs
3. UNSUPPORTED & MISLEADING CLAIMS:
   - Unsupported productivity guarantees (e.g., 'guarantees every employee becomes 10x more productive in one day')
   - Exaggerated superlatives ('best in the world', 'greatest and most amazing tool ever developed')
   - Universal absolute claims ('never need another app again', 'solves every business problem', 'guarantees perfect results', 'only platform your business will ever need')
   - Absolute security promises ('100% secure', 'bulletproof', 'impossible to breach')
   - Unsubstantiated multipliers ('guarantees 500% increase', 'double your sales')
   - Impossible performance claims ('eliminated all latency')
   - Unverified financial outcomes ('saving millions instantly')
   - Unsubstantiated replacement claims ('replaces firewalls or traditional antivirus')
4. UNNECESSARY, IRRELEVANT & EXCESSIVE CONTENT:
   - Repeated product messaging (anaphora, repeating '[Brand] is amazing. [Brand] is revolutionary. [Brand] is the best.')
   - Duplicate or unnecessary promotional sentences that reiterate earlier claims without adding new information
   - Verbatim repeated sentences or paragraphs
   - Distracting internal technical details in public-facing marketing copy
5. BRAND VOICE, TONE & READABILITY:
   - Redundant superlative stacking ('most powerful platform, the greatest platform')
   - Content quality and readability issues (monotonous cadence, excessive promotional fluff vs substance)
   - Buzzword drift (game-changer, silver bullet), informal greetings in press releases, excessive urgency pressure in ads
6. SECURITY & TECHNICAL DISCLOSURE:
   - Internal infrastructure disclosures, internal IP addresses, staging URLs

ACTIVE ORGANIZATION GUIDELINES:
{guidelines_context if guidelines_context else "Maintain authoritative, transparent, and professional communication. Prohibit unsubstantiated claims and absolute guarantees."}

CONTENT CATEGORY: {category or "General Business Copy"}
TARGET CHANNEL: {target_platform or "External Marketing"}

DRAFT CONTENT:
\"\"\"{sanitized_content}\"\"\"

Identify any violations not already handled.
Return a valid JSON array of objects. Format each item exactly as:
{{
  "category": "confidentiality" | "privacy" | "misleading_claim" | "unnecessary_content" | "brand_voice" | "security_technical",
  "module": "confidentiality" | "privacy" | "marketing_claim" | "unnecessary_content" | "brand_voice" | "security_technical",
  "severity": "critical" | "high" | "medium" | "low",
  "issue_type": "Short Descriptive Title",
  "matched_text": "exact quoted substring from draft",
  "explanation": "clear explanation of the compliance/brand risk",
  "guideline_reference": "Applicable Guideline or Legal Standard",
  "recommended_action": "Replace" | "Remove" | "Shorten" | "Verify" | "Review",
  "suggested_replacement": "recommended context-aware replacement or null if removal",
  "rationale": "why this recommendation mitigates the risk"
}}

If no additional issues are found, return [].
"""

            response = client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )

            if response and response.text:
                gemini_issues = json.loads(response.text)
                if isinstance(gemini_issues, list):
                    for g_issue in gemini_issues:
                        matched = g_issue.get("matched_text", "")
                        if matched and matched in content:
                            start_pos = content.find(matched)
                            end_pos = start_pos + len(matched)

                            # Deduplicate against existing findings
                            overlaps = False
                            g_cat = g_issue.get("category") or g_issue.get("module")
                            for existing in issues:
                                es = existing.get("char_start", 0)
                                ee = existing.get("char_end", 0)
                                ec = existing.get("category", "")
                                if ec == g_cat and max(start_pos, es) < min(end_pos, ee):
                                    overlaps = True
                                    break

                            if not overlaps:
                                g_issue["char_start"] = start_pos
                                g_issue["char_end"] = end_pos
                                g_issue["confidence"] = 0.88
                                g_issue["detection_source"] = "AI Contextual Analysis"
                                if "category" not in g_issue:
                                    g_issue["category"] = g_issue.get("module", "brand_voice")
                                if "recommended_action" not in g_issue:
                                    g_issue["recommended_action"] = "Replace" if g_issue.get("suggested_replacement") else "Review"

                                corr_type, clean_repl = determine_correction_strategy(
                                    action=g_issue["recommended_action"],
                                    replacement=g_issue.get("suggested_replacement"),
                                    category=g_issue["category"]
                                )
                                g_issue["correction_type"] = corr_type
                                g_issue["suggested_replacement"] = clean_repl
                                issues.append(g_issue)

                    logger.info(f"Layer 2 Gemini analysis complete. Total aggregated findings: {len(issues)}")
                    engine_mode = "hybrid_gemini"

        except Exception as e:
            logger.warning(f"Gemini AI analysis skipped or encountered exception: {e}. Utilizing deterministic engine.")
            engine_mode = "deterministic_fallback"

    # Sort all issues chronologically by position in the text
    issues.sort(key=lambda x: (x.get("char_start") or 0))

    # -----------------------------------------------------------------
    # Layer 3: Unified Mathematical Compliance Scoring
    # -----------------------------------------------------------------
    score, rating, counts = calculate_compliance_score(issues)
    logger.info(f"Compliance pipeline completed: Score={score:.1f}/100, Rating={rating}, Mode={engine_mode}, Critical={counts['critical']}, High={counts['high']}")

    return issues, score, rating, counts, engine_mode
