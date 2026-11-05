import re
import logging
from typing import List, Dict, Any, Optional, Set
from sqlalchemy.orm import Session

from app.models.brand_knowledge import BrandGuideline, ApprovedFact, RestrictedTerm
from app.models.analysis import IssueModule, IssueSeverity, IssueCategory

logger = logging.getLogger(__name__)


def mask_sensitive_preview(text: str, category: str) -> str:
    """Masks credentials, API keys, and private data for safe display."""
    if not text:
        return text
    if category in ["security_technical", "security"]:
        if text.startswith("AKIA") and len(text) >= 16:
            return text[:4] + "*" * (len(text) - 4)
        if "://" in text:
            # Mask user:pass in db urls
            return re.sub(r"://([^:]+):([^@]+)@", r"://\1:****@", text)
        if len(text) > 8:
            return text[:3] + "*" * (len(text) - 6) + text[-3:]
        return "*" * len(text)
    if category == "privacy":
        if "@" in text:
            parts = text.split("@")
            u = parts[0]
            masked_u = (u[:2] + "****") if len(u) > 2 else "****"
            return f"{masked_u}@{parts[1]}"
        if "-" in text and len(text) == 11 and text.replace("-", "").isdigit():
            # SSN
            return "***-**-" + text[-4:]
    return text


def run_deterministic_analysis(
    content: str,
    organization_id: str,
    db: Session,
    category: Optional[str] = None,
    target_platform: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Comprehensive multi-category deterministic compliance and data-loss prevention analysis.
    Scans the entire submitted text from beginning to end across all categories:
      A. Security & Technical Disclosure
      B. Confidential Information & Data Leakage
      C. Personal Information & Privacy Risks (PII)
      D. Unsupported & Misleading Claims
      E. Unnecessary, Irrelevant & Excessive Content
      F. Brand Voice & Communication Compliance
      G. Organization-Specific Dynamic Database Policies
    """
    if not content or not content.strip():
        logger.info("Empty content supplied for deterministic analysis. Returning zero findings.")
        return []

    logger.debug(f"Starting deterministic scan across {len(content)} characters for org {organization_id}")

    findings: List[Dict[str, Any]] = []
    occupied_spans: List[tuple] = []

    def span_overlaps(cat: str, start: int, end: int) -> bool:
        for c, s, e in occupied_spans:
            # Overlap within same category if ranges intersect
            if c == cat and max(start, s) < min(end, e):
                return True
        return False

    def add_finding(
        cat: str,
        module: str,
        severity: str,
        issue_type: str,
        matched_text: str,
        start: int,
        end: int,
        explanation: str,
        guideline_reference: str,
        recommended_action: str = "Replace",
        suggested_replacement: Optional[str] = None,
        rationale: Optional[str] = None,
        confidence: float = 1.0
    ):
        if span_overlaps(cat, start, end):
            return
        occupied_spans.append((cat, start, end))
        findings.append({
            "category": cat,
            "module": module,
            "severity": severity,
            "issue_type": issue_type,
            "matched_text": matched_text,
            "char_start": start,
            "char_end": end,
            "explanation": explanation,
            "guideline_reference": guideline_reference,
            "recommended_action": recommended_action,
            "suggested_replacement": suggested_replacement,
            "rationale": rationale or f"Recommended {recommended_action.lower()} action to maintain enterprise compliance.",
            "detection_source": "Rule Engine",
            "confidence": confidence
        })

    # =========================================================================
    # 1. SECURITY & TECHNICAL DISCLOSURES (Critical Infrastructure & Secrets)
    # =========================================================================
    security_patterns = [
        # AWS Access Key IDs
        (
            r"\b(AKIA[0-9A-Z]{16})\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Exposed AWS Access Key",
            "Hardcoded AWS access credentials detected. Exposing cloud keys in outward communications poses an immediate security breach risk.",
            "Security Policy: Zero Hardcoded Cloud Credentials",
            "Remove",
            None,
            "Remove secret immediately and execute credential rotation in AWS IAM."
        ),
        # GitHub Personal Access Tokens
        (
            r"\b(ghp_[a-zA-Z0-9]{36})\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Exposed GitHub Personal Access Token",
            "Active GitHub personal access token detected in draft content. Exposes repositories to unauthorized read/write access.",
            "Security Policy: Secret Management & Access Controls",
            "Remove",
            None,
            "Purge token from copy and revoke it immediately via GitHub Settings."
        ),
        # Slack API / Bot Tokens
        (
            r"\b(xox[baprs]-[a-zA-Z0-9-]{10,48})\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Exposed Slack API Token",
            "Slack workspace API token detected. Unauthorized entities could read internal communications.",
            "Security Policy: Secret Management",
            "Remove",
            None,
            "Revoke token from Slack API console and remove from draft."
        ),
        # Private SSH / Cryptographic Keys
        (
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY[^\n-]*-----",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Private Cryptographic Key Disclosure",
            "Asymmetric private key header detected. Cryptographic keys must never appear in business or marketing copy.",
            "Security Policy: Key Management & Cryptographic Hygiene",
            "Remove",
            None,
            "Purge private key from content and re-key affected endpoints."
        ),
        # Hardcoded Database Connection Strings
        (
            r"""\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?|redis|sqlite):\/\/[^\s"'<>]+""",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Database Connection URI Exposure",
            "Direct database connection URI detected with credentials or host specifications.",
            "Security Policy: Infrastructure Confidentiality",
            "Remove",
            None,
            "Remove connection URI and use abstract environment variable references."
        ),
        # Private Internal IP Addresses
        (
            r"\b(?:10\.\d{1,3}\.\d{1,3}\.\d{1,3}|192\.168\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[0-1])\.\d{1,3}\.\d{1,3})\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.HIGH.value,
            "Private RFC-1918 Internal IP Address",
            "Internal non-routable IP address exposed in public-facing draft. Leaks network topology details.",
            "Security Policy: Network Topology Privacy",
            "Replace",
            "cloud-hosted enterprise cluster",
            "Replaces internal network IP with approved architectural descriptor."
        ),
        # Internal Domain Endpoints
        (
            r"\b[a-zA-Z0-9_\.-]+\.(?:internal|local|corp|staging|private)\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.MEDIUM.value,
            "Internal Domain / Hostname Exposure",
            "Internal DNS name exposed. Disclosing internal hostnames aids reconnaissance for potential adversaries.",
            "Security Policy: Network Topology Privacy",
            "Replace",
            "api.acme.com",
            "Substitutes internal staging hostname with sanctioned public domain."
        ),
        # Internal Infrastructure References
        (
            r"(?i)\b(?:internal\s*(?:infrastructure|servers?|endpoints?|network|cluster|database|systems?)\s*(?:at|on|via|:)?\s*([a-zA-Z0-9_\.-]+\.[a-zA-Z]{2,}))\b",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.HIGH.value,
            "Internal Infrastructure Endpoint Disclosure",
            "Internal server or endpoint infrastructure cited directly in marketing copy. Exposing internal endpoints aids malicious reconnaissance.",
            "Security Policy: Infrastructure Confidentiality",
            "Replace",
            "secure enterprise gateway",
            "Replaces internal endpoint mention with abstract secure gateway terminology."
        ),
        # Plaintext Credential Assignments in Text
        (
            r"(?i)\b(?:api[_-]?key|access[_-]?token|secret[_-]?key|password|passwd|pwd)\s*[:=]\s*['\"]([a-zA-Z0-9_\-!@#$%^&*()+=]{8,})['\"]",
            "security_technical",
            IssueModule.SECURITY_TECHNICAL.value,
            IssueSeverity.CRITICAL.value,
            "Plaintext Credential / Secret Exposure",
            "Plaintext secret assignment detected in draft content.",
            "Security Policy: Zero Plaintext Credentials",
            "Remove",
            None,
            "Remove plaintext secret assignment and rotate credentials."
        )
    ]

    for pat, cat, mod, sev, itype, expl, gref, action, repl, rat in security_patterns:
        for match in re.finditer(pat, content):
            add_finding(
                cat=cat,
                module=mod,
                severity=sev,
                issue_type=itype,
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=expl,
                guideline_reference=gref,
                recommended_action=action,
                suggested_replacement=repl,
                rationale=rat
            )

    # =========================================================================
    # 2. CONFIDENTIAL INFORMATION & DATA LEAKAGE (Client, Financial, Projects)
    # =========================================================================
    confidential_patterns = [
        # Explicit Non-Public / Embargo / Internal Only Disclaimers
        (
            r"(?i)\b(?:not\s*(?:yet\s*)?approved\s*for\s*public\s*(?:release|disclosure|distribution|consumption|use)|under\s*embargo|embargoed\s*until|strictly\s*confidential|for\s*internal\s*use\s*only|internal\s*only\s*-\s*do\s*not\s*distribute)\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Explicit Publication Restriction / Embargo Notice",
            "Content explicitly marked as not approved for public release or under embargo detected in draft copy.",
            "Brand Policy: Publication Governance & Embargo Management",
            "Remove",
            None,
            "Remove embargoed material until official corporate clearance is granted."
        ),
        # Confidential Institutional Client & Banking Relationship Mentions
        (
            r"(?i)\b(?:confidential|internal|private|undisclosed|secret)\s+(?:(?:tier-\d+|fortune\s*\d+|enterprise|banking|financial|defense|government|healthcare|strategic|[a-zA-Z0-9-]+)\s+){0,3}(?:clients?|customers?|partners?|accounts?|deals?|contracts?)(?:\s+(?:JPMorgan(?:\s*Chase)?|Goldman\s*Sachs|Morgan\s*Stanley|Citigroup|Citibank|Bank\s*of\s*America|Wells\s*Fargo|Barclays|HSBC|UBS|Deutsche\s*Bank|[A-Z][a-zA-Z0-9&]+))?\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Confidential Client & Relationship Disclosure",
            "Explicit disclosure of confidential customer, partner, or institutional banking relationships violates client NDAs.",
            "Brand Policy: Customer Privacy & Non-Disclosure Agreements",
            "Replace",
            "authorized enterprise financial partners",
            "Substitutes confidential client terminology with authorized, non-disclosing partnership language."
        ),
        # Named Major Institutional Financial Clients in Client Context
        (
            r"(?i)\b(?:(?:confidential|private|undisclosed|tier-\d+)\s*(?:client|customer|partner)?\s*(?:at|with|for)?\s*)(JPMorgan(?:\s*Chase)?|Goldman\s*Sachs|Morgan\s*Stanley|Citigroup|Citibank|Bank\s*of\s*America|Wells\s*Fargo|Barclays|HSBC|UBS|Deutsche\s*Bank|Credit\s*Suisse|BNP\s*Paribas)\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Confidential Banking Client Identity Disclosure",
            "Disclosing specific institutional banking clients under confidential testing or deployment contracts breaches non-disclosure agreements.",
            "Brand Policy: Customer Privacy & Non-Disclosure Agreements",
            "Replace",
            "our enterprise banking clients",
            "Anonymizes specific bank identity to preserve mutual client NDA protections."
        ),
        # Non-Public Revenue Figures & High-Value Deals
        (
            r"(?i)(?:\$\d+(?:\.\d+)?\s*(?:million|billion|trillion|m|b)\s*(?:in\s*(?:revenue|sales|profit|ebitda|arr|mrr|gross\s*margin))|\brevenue\s*(?:of\s*)?\$\d+(?:\.\d+)?\s*(?:million|billion|trillion|m|b))\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Non-Public Financial Figures Disclosure",
            "Specific dollar revenue metrics must not be disclosed in public-facing marketing copy prior to certified corporate financial release.",
            "Corporate Policy: Regulation Fair Disclosure (Reg FD)",
            "Remove",
            None,
            "Purge specific dollar earnings from promotional content."
        ),
        # Internal Non-Public Profit Margins / EBITDA / Burn Rate
        (
            r"(?i)(?:\b(?:expected|projected|internal)?\s*(?:profit\s*margins?|gross\s*margins?|operating\s*margins?)\s*(?:of\s*)?\d+(?:\.\d+)?%|\b(?:internal\s*(?:margins?|ebitda|burn\s*rate|run\s*rate|revenue\s*figures?|financials?|kpis?|q[1-4]\s*financials?)|gross\s*margin\s*of\s*\d+%\s*\(internal\)|confidential\s*revenue\s*run-rate))",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Confidential Profit Margin / Financial Metrics Leak",
            "Internal financial metrics (profit margins, EBITDA, burn-rate, non-public margin data) cannot be published prior to certified SEC/financial earnings disclosure.",
            "Corporate Policy: Regulation Fair Disclosure (Reg FD)",
            "Remove",
            None,
            "Purge unannounced internal margin percentages from external communications."
        ),
        # Internal Project Names & Unreleased Products
        (
            r"(?i)\b(?:internal\s+project\s+[a-z0-9_-]+|project\s+(?:apollo|titan|phoenix|olympus|alpha|omega|black|stealth|x|y|z)\b|project\s+(?!(?:management|tracking|planning|plans?|tasks?|workflows?|dashboards?|updates?|timelines?|files?|overview|scope|details|deliverables|reports?)\b)[A-Z][a-zA-Z0-9_-]+|code-?named?\s+['\"][^'\"]+['\"]|unreleased\s+(?:feature|version|v\d+|module))\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.HIGH.value,
            "Internal Project Name / Unreleased Product Disclosure",
            "Internal project codename or unreleased product roadmap detected in outward messaging.",
            "Brand Policy: Product Marketing Confidentiality",
            "Replace",
            "upcoming enterprise platform release",
            "Replaces internal project codename with generalized product launch terminology."
        ),
        # Private Deals, Mergers, Unannounced Acquisitions
        (
            r"(?i)\b(?:non-disclosure\s*agreement|nda\s*terms|confidential\s*settlement|unannounced\s*acquisition|stealth\s*merger|confidential\s*deal\s*terms?)\b",
            "confidentiality",
            IssueModule.CONFIDENTIALITY.value,
            IssueSeverity.CRITICAL.value,
            "Confidential Transaction / NDA Disclosure",
            "References to confidential transactions, NDA terms, or private settlements are strictly prohibited in public marketing copy.",
            "Legal Governance: Commercial Confidentiality Obligations",
            "Remove",
            None,
            "Remove references to private agreements or ongoing commercial negotiations."
        )
    ]

    for pat, cat, mod, sev, itype, expl, gref, action, repl, rat in confidential_patterns:
        for match in re.finditer(pat, content):
            add_finding(
                cat=cat,
                module=mod,
                severity=sev,
                issue_type=itype,
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=expl,
                guideline_reference=gref,
                recommended_action=action,
                suggested_replacement=repl,
                rationale=rat
            )

    # Location Disclosure Linked to Confidential Engagements
    # Example: "After testing with our confidential Tier-1 banking clients in New York..."
    location_in_client_ctx = re.compile(
        r"(?i)(?:confidential|private|undisclosed|tier-\d+)[^\.\n,;]+?(?:in\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*))"
    )
    for m in location_in_client_ctx.finditer(content):
        loc = m.group(1)
        if loc and loc.lower() in ["new york", "london", "tokyo", "singapore", "chicago", "san francisco", "zurich", "frankfurt"]:
            start = m.start(1)
            end = m.end(1)
            add_finding(
                cat="confidentiality",
                module=IssueModule.CONFIDENTIALITY.value,
                severity=IssueSeverity.MEDIUM.value,
                issue_type="Sensitive Client Geographic Identifier",
                matched_text=loc,
                start=start,
                end=end,
                explanation=f"Citing specific metropolitan headquarters ('{loc}') in conjunction with private/confidential client work increases de-anonymization risk.",
                guideline_reference="Brand Policy: Customer Privacy & Non-Disclosure Agreements",
                recommended_action="Replace",
                suggested_replacement="leading global financial centers",
                rationale="Replaces specific client city with generalized geographic scope to preserve confidentiality."
            )

    # =========================================================================
    # 3. PERSONAL INFORMATION & PRIVACY RISKS (PII)
    # =========================================================================
    # Personal Email Addresses
    email_pattern = re.compile(r"\b([A-Za-z0-9._%+-]+@(?!acme\.com|contentguard\.demo|example\.com|domain\.com)[A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")
    for match in email_pattern.finditer(content):
        add_finding(
            cat="privacy",
            module=IssueModule.PRIVACY.value,
            severity=IssueSeverity.HIGH.value,
            issue_type="Personally Identifiable Information (Email)",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Personal email address detected in draft copy. Personal contact details should not be exposed in public communications.",
            guideline_reference="Privacy Governance: GDPR & CCPA Data Minimization",
            recommended_action="Replace",
            suggested_replacement="contact@company.com",
            rationale="Substitutes private personal email with generic organizational department mailbox."
        )

    # Phone Numbers
    phone_pattern = re.compile(r"\b(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
    for match in phone_pattern.finditer(content):
        if "555-0199" not in match.group():
            add_finding(
                cat="privacy",
                module=IssueModule.PRIVACY.value,
                severity=IssueSeverity.HIGH.value,
                issue_type="Personally Identifiable Information (Phone Number)",
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation="Specific telephone contact number detected in copy. May expose employee or client direct dial lines.",
                guideline_reference="Privacy Governance: PII & Contact Information Policy",
                recommended_action="Replace",
                suggested_replacement="+1 (800) 555-0199",
                rationale="Replaces direct line with verified enterprise customer support number."
            )

    # Social Security Numbers (SSN)
    ssn_pattern = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
    for match in ssn_pattern.finditer(content):
        add_finding(
            cat="privacy",
            module=IssueModule.PRIVACY.value,
            severity=IssueSeverity.CRITICAL.value,
            issue_type="National Identity Identifier (SSN)",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Format matches United States Social Security Number. Severe privacy violation.",
            guideline_reference="Privacy Policy: Zero Sensitive PII Disclosure",
            recommended_action="Remove",
            suggested_replacement=None,
            rationale="Immediately delete government identifier from outward copy."
        )

    # Credit Card Numbers
    cc_pattern = re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b")
    for match in cc_pattern.finditer(content):
        add_finding(
            cat="privacy",
            module=IssueModule.PRIVACY.value,
            severity=IssueSeverity.CRITICAL.value,
            issue_type="Payment Card Industry Data (Credit Card)",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="16-digit payment card number detected. Violates PCI-DSS standards.",
            guideline_reference="Financial Compliance: PCI-DSS Data Protection",
            recommended_action="Remove",
            suggested_replacement=None,
            rationale="Immediately purge payment card numbers from all outward content."
        )

    # Residential Physical Street Addresses
    address_pattern = re.compile(r"\b\d{1,5}\s+[A-Za-z0-9\s,]{3,30}(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Lane|Ln|Drive|Dr|Court|Ct)\b")
    for match in address_pattern.finditer(content):
        add_finding(
            cat="privacy",
            module=IssueModule.PRIVACY.value,
            severity=IssueSeverity.MEDIUM.value,
            issue_type="Physical / Residential Address Disclosure",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Specific street address identified in copy. Residential or unverified physical addresses pose safety and privacy concerns.",
            guideline_reference="Privacy Standards: Address & Facility Privacy",
            recommended_action="Replace",
            suggested_replacement="100 Enterprise Way, Suite 400",
            rationale="Substitutes private physical location with official corporate facility address."
        )

    # =========================================================================
    # 4. UNSUPPORTED & MISLEADING CLAIMS (Guarantees, Multipliers, Supremacy)
    # =========================================================================
    claims_rules = [
        # Absolute Security & Invulnerability Claims (100% security, 100% secure, guarantees 100% security)
        (
            r"(?i)\b(?:guarantees?\s*(?:100%\s*)?(?:security|protection|safety)|100%\s*(?:security|secure|safe|protection|protected)|unhackable|impenetrable|unbreakable\s*security)\b",
            IssueSeverity.CRITICAL.value,
            "Absolute Security Claim",
            "Absolute security assertions expose the enterprise to catastrophic breach liability. Security must be stated via verified compliance standards.",
            "Brand Policy: Security & Risk Compliance",
            "Replace",
            "SOC-2 Type II certified secure architecture",
            "Substitutes an unprovable absolute claim with verified third-party audit credentials."
        ),
        # Completely eliminates every cybersecurity risk / zero risk
        (
            r"(?i)\b(?:completely\s*eliminates?\s*(?:every|all)\s*(?:cybersecurity\s*|security\s*)?risks?|eliminates?\s*(?:all|every)\s*(?:cybersecurity\s*|security\s*)?risks?|zero\s*(?:cybersecurity\s*)?risk)\b",
            IssueSeverity.CRITICAL.value,
            "Absolute Risk Elimination Claim",
            "Claims that a system 'completely eliminates all risks' are impossible in information security and violate trade regulations against deceptive claims.",
            "Brand Policy: Security & Risk Compliance",
            "Replace",
            "substantially mitigates common cybersecurity risks",
            "Replaces impossible zero-risk assertion with responsible, defensible mitigation language."
        ),
        # No hacker in the world can ever breach our infrastructure / impossible to breach
        (
            r"(?i)\b(?:no\s*hacker(?:\s*in\s*the\s*world)?\s*(?:can|could)\s*(?:ever\s*)?breach(?:\s*our\s*infrastructure|\s*your\s*infrastructure)?|impossible\s*(?:for\s*hackers\s*)?to\s*breach(?:\s*your\s*infrastructure|\s*our\s*infrastructure)?|invulnerable\s*to\s*(?:all\s*)?(?:hackers?|cyberattacks?|breaches?))\b",
            IssueSeverity.CRITICAL.value,
            "Absolute Invulnerability Assertion",
            "Claiming that 'no hacker can ever breach' infrastructure violates cybersecurity governance guidelines and creates legal vulnerability.",
            "Brand Policy: Security & Risk Compliance",
            "Replace",
            "engineered with multi-layered defense-in-depth security controls",
            "Shifts terminology to recognized security industry best-practice controls."
        ),
        # Completely bulletproof data solution / platform
        (
            r"(?i)\b(?:completely\s*bulletproof(?:\s+[a-z]+){1,3}|bulletproof\s*(?:data\s*solution|security|system|platform|solution))\b",
            IssueSeverity.CRITICAL.value,
            "Exaggerated Reliability Claim (Bulletproof)",
            "Terms like 'completely bulletproof' constitute unsubstantiated technical guarantees that create false expectations of zero failure.",
            "Brand Policy: Verifiable Technical Claims",
            "Replace",
            "resilient, enterprise-grade data architecture",
            "Replaces hyperbolic 'bulletproof' terminology with validated architectural resiliency language."
        ),
        # Perpetual SLA Guarantee (99.9% uptime SLA forever / uptime SLA forever)
        (
            r"(?i)\b(?:(?:99(?:\.\d+)?%|100%)\s*uptime\s*sla\s*forever|uptime\s*sla\s*forever|forever\s*uptime|guaranteed\s*uptime\s*forever|never\s*goes?\s*down)\b",
            IssueSeverity.HIGH.value,
            "Perpetual Unsupported SLA Guarantee",
            "Promising uptime SLAs 'forever' without contractual qualification constitutes an unachievable perpetual guarantee.",
            "Brand Policy: Verifiable Technical Claims",
            "Replace",
            "verified 99.9% uptime SLA",
            "Removes speculative perpetual commitment while preserving verified SLA metrics."
        ),
        # Replaces firewalls or traditional antivirus software
        (
            r"(?i)\b(?:replaces?\s*the\s*need\s*for\s*(?:third-party\s*)?(?:firewalls?|traditional\s*antivirus(?:\s*software)?|endpoint\s*security)(?:\s*(?:or|and)\s*(?:traditional\s*)?(?:firewalls?|antivirus(?:\s*software)?|endpoint\s*security))*|eliminates?\s*the\s*need\s*for\s*(?:firewalls?|antivirus|security\s*teams?|audits?))\b",
            IssueSeverity.CRITICAL.value,
            "Dangerous Security Replacement Claim",
            "Claiming to replace foundational security controls (firewalls, antivirus) constitutes dangerous and legally irresponsible marketing.",
            "Security Policy: Co-existence & Complementary Architecture",
            "Replace",
            "integrates seamlessly alongside your existing firewalls and endpoint protection suite",
            "Re-frames solution as complementary to existing defense-in-depth infrastructure."
        ),
        # Eliminated all system latency / zero latency
        (
            r"(?i)\b(?:eliminated?\s*all\s*(?:system\s*)?latency|zero\s*latency|latency-free)\b",
            IssueSeverity.HIGH.value,
            "Impossible Performance Claim (Zero Latency)",
            "Physics and distributed systems dictate that latency cannot be 'completely eliminated'. Marketing must cite empirically tested thresholds.",
            "Brand Policy: Verifiable Technical Claims",
            "Replace",
            "substantially minimized system latency to sub-millisecond thresholds",
            "Provides an accurate, defensible engineering performance statement."
        ),
        # Percentage Multiplier (improved efficiency by 500% / guarantees 500% increase)
        (
            r"(?i)\b(?:improved?|boosted?|increased?|accelerated?|optimized?|enhanced?)\s+(?:[a-zA-Z]+\s+){0,4}by\s*\d{2,4}%",
            IssueSeverity.CRITICAL.value,
            "Unsubstantiated Performance Multiplier",
            "Claiming multi-hundred percent operational improvements without published case studies violates promotional accuracy standards.",
            "Writing Rules: Verifiable Empirical Claims",
            "Replace",
            "substantially accelerated operational workflows",
            "Substitutes speculative percentage multiplier with validated operational efficiency language."
        ),
        (
            r"(?i)\b(?:guarantees?\s*(?:a\s*)?)?(\d{2,4}%)\s*(?:increase|boost|growth|reduction|savings|drop|improvement|roi|gain|efficiency)\b",
            IssueSeverity.CRITICAL.value,
            "Unsubstantiated Multiplier Guarantee",
            "Promising a guaranteed multi-hundred percent gain violates consumer protection and fair marketing regulations without published peer-reviewed benchmarks.",
            "Writing Rules: Verifiable Empirical Claims",
            "Replace",
            "delivers measurable velocity improvements across enterprise workflows",
            "Replaces speculative percentage multiplier with validated operational velocity benefits."
        ),
        # Zero Incidents / Zero Breaches Claim
        (
            r"(?i)\b(?:zero\s*(?:security\s*)?incidents?|100%\s*incident-free|zero\s*breaches?|never\s*(?:been\s*)?breached)\b",
            IssueSeverity.HIGH.value,
            "Unverified Performance Claim (Zero Incidents)",
            "Asserting zero security incidents without audited telemetry claims invulnerability and exposes the organization to misrepresentation liabilities.",
            "Brand Policy: Verifiable Technical Claims",
            "Replace",
            "a rigorously monitored security posture",
            "Replaces unverified zero-incident claim with active monitoring assurance."
        ),
        # Saving you millions of dollars instantly
        (
            r"(?i)\b(?:saving\s*(?:you\s*)?millions(?:\s*of\s*dollars)?\s*instantly|saves?\s*millions\s*instantly|instant\s*millions|generate\s*millions\s*overnight)\b",
            IssueSeverity.HIGH.value,
            "Unsupported Financial Outcome Claim",
            "Unsubstantiated promises of 'saving millions instantly' trigger aggressive consumer protection scrutiny and lack empirical grounding.",
            "Brand Policy: Zero Unsubstantiated Financial Outcome Claims",
            "Replace",
            "driving significant operational cost efficiencies over time",
            "Substitutes get-rich hyperbolic savings with sustainable operational efficiency terminology."
        ),
        # 100% Risk-Free / Money-Back Guarantees
        (
            r"(?i)\b(?:100%\s*(?:risk-free(?:\s*guarantee)?|guaranteed|safe|fail-safe)|risk-free\s*guarantee|money-back\s*guarantee|zero-risk)\b",
            IssueSeverity.CRITICAL.value,
            "Prohibited Absolute Guarantee",
            "Absolute risk-free guarantees violate commercial compliance policy. Marketing copy must acknowledge terms and standard operating conditions.",
            "Brand Policy: Zero Absolute Performance Guarantees",
            "Replace",
            "enterprise-grade reliability assurance",
            "Mitigates legal liability by substituting absolute guarantee with substantiated reliability terminology."
        ),
        # General Unqualified Commercial Guarantees
        (
            r"(?i)\b(?:guaranteed\s*(?:growth|roi|revenue|profit|results|success|leads|conversions?)|guarantee\s*success)\b",
            IssueSeverity.HIGH.value,
            "Unqualified Commercial Guarantee",
            "Guarantees of commercial outcomes must include qualification disclaimers and audited performance scope.",
            "Brand Policy: Zero Absolute Performance Guarantees",
            "Replace",
            "proven acceleration of business performance",
            "Removes unqualified promise while maintaining strong value proposition."
        ),
        # Specific Productivity & Performance Guarantees (10x productivity in 1 day)
        (
            r"(?i)\b(?:guarantees?\s+(?:that\s+)?(?:every|all|any)\s+(?:employee|worker|team|user|developer|agent)s?\s+will\s+(?:become|be)\s+(?:\d{1,4}\s*(?:times|x)|(?:\d{1,3}%))\s+more\s+(?:productive|efficient|effective|fast)(?:\s+(?:within|in)\s+[^\.\n,;]+)?)\b",
            IssueSeverity.HIGH.value,
            "Unsupported Productivity Guarantee",
            "Specific performance and productivity improvement is promised without verifiable empirical evidence or published benchmark audits.",
            "Brand Policy: Verifiable Technical & Productivity Claims",
            "Replace",
            "designed to streamline daily workflows and improve team productivity",
            "Replaces speculative multiplier guarantee with verified workflow productivity benefits."
        ),
        # Universal Absolute Need Claim ("never need another ... again")
        (
            r"(?i)\b(?:you\s+will\s+never\s+need\s+another\s+[a-zA-Z\s]{3,35}\s+again|never\s+need\s+another\s+[a-zA-Z\s]{3,35}\s+again)\b",
            IssueSeverity.HIGH.value,
            "Universal Absolute Need Claim",
            "Claiming customers 'will never need another application again' is an unprovable absolute assertion that creates false customer expectations.",
            "Brand Policy: Zero Absolute Guarantees",
            "Replace",
            "centralizes your core productivity workflows in a single workspace",
            "Frames the value proposition as a unified workspace without making unprovable exclusivity claims."
        ),
        # Universal Problem-Solving Claim ("solves every business problem")
        (
            r"(?i)\b(?:solves?\s+(?:every|all)\s*(?:business\s*|enterprise\s*|operational\s*|customer\s*|workflow\s*)?problems?)\b",
            IssueSeverity.HIGH.value,
            "Absolute Problem-Solving Claim",
            "Asserting that software 'solves every business problem' is a universal absolute claim that cannot be guaranteed or substantiated.",
            "Brand Policy: Verifiable Technical Claims",
            "Replace",
            "addresses key business and operational workflow challenges",
            "Replaces universal panacea claim with targeted capability statement."
        ),
        # Absolute Results Guarantee ("guarantees perfect results")
        (
            r"(?i)\b(?:guarantees?\s+(?:perfect|flawless|100%|absolute|unfailing)\s+results?)\b",
            IssueSeverity.HIGH.value,
            "Absolute Results Guarantee",
            "Promising 'perfect results' is an absolute guarantee prohibited under commercial consumer protection and advertising guidelines.",
            "Brand Policy: Zero Absolute Performance Guarantees",
            "Replace",
            "delivers consistent, high-quality results across projects",
            "Replaces absolute perfection guarantee with defensible quality assurance language."
        ),
        # Exclusivity Absolute Claim ("only platform your business will ever need")
        (
            r"(?i)\b(?:the\s+only\s+(?:platform|tool|application|software|solution|app)\s+(?:your\s+business|you|anyone)\s+will\s+ever\s+need)\b",
            IssueSeverity.HIGH.value,
            "Exclusivity Absolute Claim",
            "Claiming to be 'the only platform your business will ever need' is an unsubstantiated absolute exclusivity statement.",
            "Tone & Voice: Objective & Defensible Product Positioning",
            "Replace",
            "a comprehensive platform designed to support your team's expanding needs",
            "Replaces absolute exclusivity with forward-looking platform capability."
        ),
        # Relative / General Productivity Multiplier ("10 times more productive")
        (
            r"(?i)\b(?:\d{1,4}\s*(?:times|x))\s+more\s+(?:productive|efficient|effective|profitable|faster|speedy)\b",
            IssueSeverity.HIGH.value,
            "Unsubstantiated Performance Multiplier",
            "Numerical productivity claims (e.g. '10 times more productive') require published customer case studies to comply with advertising substantiation laws.",
            "Writing Rules: Verifiable Empirical Claims",
            "Replace",
            "substantially more productive",
            "Replaces unsubstantiated numeric multiplier with defensible qualitative benefit."
        ),
        # Absolute Superiority ("best ... in the world")
        (
            r"(?i)\b(?:the\s+)?best\s+(?:[a-zA-Z\s]{0,30})\s*in\s+the\s+world\b",
            IssueSeverity.MEDIUM.value,
            "Exaggerated Superlative (Best in the World)",
            "Claiming to be 'the best in the world' lacks independent, verified third-party comparative proof and reduces credibility.",
            "Brand Guidelines: Authoritative, Transparent, and Professional",
            "Replace",
            "a leading enterprise productivity platform",
            "Replaces superlative claim with accepted enterprise positioning."
        ),
        # Greatest and most amazing tool ever developed
        (
            r"(?i)\b(?:the\s+)?greatest\s+(?:and\s+most\s+[a-zA-Z]+|\s*tool|\s*platform|\s*solution)?\s*(?:tool|platform|solution|product)?\s*ever\s*(?:developed|created|built|released)\b",
            IssueSeverity.MEDIUM.value,
            "Exaggerated Superlative Claim",
            "Claims of being the 'greatest and most amazing tool ever developed' are hyperbolic promotional assertions that violate objective brand voice standards.",
            "Brand Guidelines: Objective & Factual Messaging",
            "Replace",
            "a powerful and modern productivity tool",
            "Replaces hyperbolic praise with professional descriptive language."
        ),
        # Redundant Superlative Stacking ("most powerful platform, the greatest platform")
        (
            r"(?i)\b(?:the\s+)?most\s+powerful\s+platform,\s+the\s+greatest\s+platform\b",
            IssueSeverity.MEDIUM.value,
            "Redundant Superlative Stacking",
            "Stacking repetitive superlatives ('most powerful platform, the greatest platform') adds no informational value and weakens readability.",
            "Editorial Standards: Editorial Conciseness & Precision",
            "Replace",
            "a versatile and scalable platform",
            "Consolidates repetitive superlatives into clear descriptive capability."
        ),
        # Unsubstantiated Multipliers (double / triple / 10x)
        (
            r"(?i)\b(?:double|triple|10x|5x|100x)\s*(?:your\s*)?(?:leads|sales|revenue|traffic|growth|conversions?|speed)\b",
            IssueSeverity.HIGH.value,
            "Unsubstantiated Multiplier Claim",
            "Universal multiplier promises are prohibited without citing verified customer segment case studies.",
            "Writing Rules: Verifiable Empirical Claims",
            "Replace",
            "significantly optimize lead generation efficiency",
            "Replaces speculative multiplier with measurable efficiency language."
        ),
        # Unsupported Superiority (#1 in the world, etc.)
        (
            r"(?i)\b(?:no\s*other\s*competitor\s*can\s*match|unmatched\s*by\s*anyone|better\s*than\s*all\s*competitors|crush(?:ing)?\s*the\s*competition|#1\s*in\s*the\s*world|best\s*in\s*the\s*world|the\s*only\s*solution\s*that)\b",
            IssueSeverity.HIGH.value,
            "Unsupported Superiority Claim",
            "Absolute superiority statements require accredited third-party comparative research to avoid unfair competition penalties.",
            "Tone & Voice: Authoritative, Transparent, and Professional",
            "Replace",
            "designed to outperform legacy manual workflows",
            "Focuses on architectural capability rather than legally vulnerable competitive assertions."
        )
    ]

    for pat, sev, itype, expl, gref, action, repl, rat in claims_rules:
        for match in re.finditer(pat, content):
            add_finding(
                cat="misleading_claim",
                module=IssueModule.MARKETING_CLAIM.value,
                severity=sev,
                issue_type=itype,
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=expl,
                guideline_reference=gref,
                recommended_action=action,
                suggested_replacement=repl,
                rationale=rat
            )

    # =========================================================================
    # 5. UNNECESSARY, IRRELEVANT & EXCESSIVE CONTENT (Duplicates & Clutter)
    # =========================================================================
    # Intra-Sentence and Phrase Repetition (e.g. "X is X" or "upcoming release is upcoming release")
    phrase_repeat_pattern = re.compile(
        r"\b([a-zA-Z0-9_-]+(?:\s+[a-zA-Z0-9_-]+){2,})\s+(?:is|and|,|-|was|are)?\s*\1\b",
        re.IGNORECASE
    )
    for match in phrase_repeat_pattern.finditer(content):
        add_finding(
            cat="unnecessary_content",
            module=IssueModule.UNNECESSARY_CONTENT.value,
            severity=IssueSeverity.MEDIUM.value,
            issue_type="Repeated Phrase Redundancy",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Unintentional duplicated phrase detected within the sentence. Eliminating redundant repetition improves editorial clarity.",
            guideline_reference="Editorial Standards: Conciseness & Redundancy Minimization",
            recommended_action="Replace",
            suggested_replacement=match.group(1),
            rationale="Removes duplicate repetition to maintain clean editorial cadence."
        )

    # Anaphora / Repetitive Sentence Starts (e.g. "SmartWork AI is amazing. SmartWork AI is revolutionary. SmartWork AI is the best.")
    repetitive_starts_pattern = re.compile(
        r"(?i)\b(([A-Z][a-zA-Z0-9_\s]{2,20})\s+is\s+(?:the\s+)?[a-zA-Z]+[.!?]\s+(\2\s+is\s+(?:the\s+)?[a-zA-Z]+[.!?]\s*)+)"
    )
    for match in repetitive_starts_pattern.finditer(content):
        add_finding(
            cat="unnecessary_content",
            module=IssueModule.UNNECESSARY_CONTENT.value,
            severity=IssueSeverity.MEDIUM.value,
            issue_type="Repeated Product Messaging (Repetitive Cadence)",
            matched_text=match.group(1).strip(),
            start=match.start(),
            end=match.end(),
            explanation="Repetitive sentence structure ('[Subject] is X. [Subject] is Y. [Subject] is Z.') creates a monotonous cadence and reads like repetitive marketing chanting.",
            guideline_reference="Editorial Standards: Sentence Variety & Readability",
            recommended_action="Replace",
            suggested_replacement="delivers an innovative, high-performance workspace for modern teams",
            rationale="Combines fragmented repetitive sentences into a single cohesive, professional statement."
        )

    # Duplicate or Unnecessary Promotional Sentences
    # Detects redundant, superfluous promotional sentences that chain multiple superlatives / exclusivity claims
    # without introducing factual product specifications or evidence.
    unnecessary_promo_patterns = [
        (
            r"(?i)\b(?:(?:it|this|our\s+software|our\s+platform)\s+is\s+)?(?:the\s+)?(?:most\s+[a-z]+|greatest|best|fastest|smartest)\s+(?:platform|tool|solution|product|software|app)(?:,\s+(?:the\s+)?(?:greatest|best|most\s+[a-z]+|fastest|smartest)\s+(?:platform|tool|solution|product|software|app))+\s*,?\s*(?:and\s+)?(?:the\s+)?only\s+(?:platform|tool|solution|product|software|app)\s+(?:your\s+business|you|anyone)\s+will\s+ever\s+need[.\!]*",
            IssueSeverity.MEDIUM.value,
            "Duplicate or Unnecessary Promotional Sentence",
            "This sentence chains redundant promotional superlatives that repeat previously stated claims without providing new information or functional capabilities.",
            "Editorial Standards: Conciseness & Information Density",
            "Remove",
            None,
            "Removes redundant promotional restatements to increase information density and streamline reader experience."
        ),
        (
            r"(?i)\b(?:(?:it|this)\s+is\s+)?(?:the\s+)?(?:greatest|best|most\s+powerful|most\s+revolutionary)\s+(?:platform|tool|solution|product),\s+(?:the\s+)?(?:greatest|best|most\s+powerful|most\s+revolutionary)\s+(?:platform|tool|solution|product)\b[^\.\n]*",
            IssueSeverity.MEDIUM.value,
            "Duplicate or Unnecessary Promotional Sentence",
            "Repetitive promotional claim stacking detected. Repeating product descriptors adds no informational value.",
            "Editorial Standards: Conciseness & Information Density",
            "Replace",
            "a scalable platform designed for modern business workflows",
            "Replaces repetitive promotional stacking with a concise capability statement."
        )
    ]
    for p_pat, p_sev, p_type, p_expl, p_gref, p_action, p_repl, p_rat in unnecessary_promo_patterns:
        for match in re.finditer(p_pat, content):
            add_finding(
                cat="unnecessary_content",
                module=IssueModule.UNNECESSARY_CONTENT.value,
                severity=p_sev,
                issue_type=p_type,
                matched_text=match.group().strip(),
                start=match.start(),
                end=match.end(),
                explanation=p_expl,
                guideline_reference=p_gref,
                recommended_action=p_action,
                suggested_replacement=p_repl,
                rationale=p_rat
            )

    # Repeated Product Messaging Across Paragraphs (e.g. repeated "X is the best" / "X is amazing")
    claim_phrases = [
        r"(?i)\b(?:[A-Z][a-zA-Z0-9_\s]{2,20}\s+is\s+(?:the\s+)?best)\b",
        r"(?i)\b(?:[A-Z][a-zA-Z0-9_\s]{2,20}\s+is\s+amazing)\b",
        r"(?i)\b(?:[A-Z][a-zA-Z0-9_\s]{2,20}\s+is\s+revolutionary)\b"
    ]
    for c_pat in claim_phrases:
        matches = list(re.finditer(c_pat, content))
        if len(matches) > 1:
            for m in matches[1:]:
                add_finding(
                    cat="unnecessary_content",
                    module=IssueModule.UNNECESSARY_CONTENT.value,
                    severity=IssueSeverity.MEDIUM.value,
                    issue_type="Repeated Product Messaging",
                    matched_text=m.group(),
                    start=m.start(),
                    end=m.end(),
                    explanation=f"The promotional claim '{m.group()}' is repeated multiple times throughout the copy. Repetitive messaging reduces content polish and reader engagement.",
                    guideline_reference="Editorial Standards: Redundancy Minimization",
                    recommended_action="Remove",
                    suggested_replacement="",
                    rationale="Eliminating repetitive messaging avoids reader fatigue and improves brand professionalism."
                )

    # Duplicate Full Sentence Detection
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", content) if len(s.strip()) > 25]
    seen_sentences: Dict[str, tuple] = {}
    for s in sentences:
        s_norm = re.sub(r"\s+", " ", s.lower())
        if s_norm in seen_sentences:
            orig_start, orig_end = seen_sentences[s_norm]
            for m in re.finditer(re.escape(s), content):
                if m.start() != orig_start:
                    add_finding(
                        cat="unnecessary_content",
                        module=IssueModule.UNNECESSARY_CONTENT.value,
                        severity=IssueSeverity.LOW.value,
                        issue_type="Redundant Duplicate Sentence",
                        matched_text=m.group(),
                        start=m.start(),
                        end=m.end(),
                        explanation="This sentence is duplicated verbatim elsewhere in the draft. Eliminating duplicate copy improves clarity and punchiness.",
                        guideline_reference="Editorial Standards: Conciseness & Redundancy Minimization",
                        recommended_action="Remove",
                        suggested_replacement="",
                        rationale="Removing duplicate content avoids reader fatigue and improves conciseness."
                    )
                    break
        else:
            for m in re.finditer(re.escape(s), content):
                seen_sentences[s_norm] = (m.start(), m.end())
                break

    # Technical Stack Traces or SQL Queries in Public Copy
    tech_clutter_pattern = re.compile(r"(?i)\b(?:select\s+\*\s+from\s+[a-z0-9_]+|traceback\s+\(most\s+recent\s+call\s+last\)|exception\s+in\s+thread|nullpointerexception)\b")
    for match in tech_clutter_pattern.finditer(content):
        add_finding(
            cat="unnecessary_content",
            module=IssueModule.UNNECESSARY_CONTENT.value,
            severity=IssueSeverity.MEDIUM.value,
            issue_type="Internal Debugging / SQL Clutter",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Low-level technical debugging traces or raw SQL statements detected in public-facing copy.",
            guideline_reference="Editorial Standards: Audience Alignment & Clarity",
            recommended_action="Remove",
            suggested_replacement="",
            rationale="Removes distracting and unprofessional technical code fragments from public messaging."
        )

    # =========================================================================
    # 6. BRAND VOICE & JARGON (Buzzwords, Superlatives, Format Constraints)
    # =========================================================================
    # Excessive Chained Superlatives & Hyperbolic Language
    chained_superlatives_pattern = re.compile(
        r"(?i)\b(?:the\s*)?(?:biggest|greatest|most\s*powerful|most\s*advanced|most\s*revolutionary|best|fastest|smartest)(?:,\s*(?:biggest|greatest|most\s*powerful|most\s*advanced|most\s*revolutionary|best|fastest|smartest|and\s*most\s*[a-z]+))+\s*(?:product|platform|tool|solution)?\s*(?:ever\s*created)?\b"
    )
    for match in chained_superlatives_pattern.finditer(content):
        add_finding(
            cat="brand_voice",
            module=IssueModule.BRAND_VOICE.value,
            severity=IssueSeverity.MEDIUM.value,
            issue_type="Excessive Superlatives & Hyperbolic Fluff",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation="Chained superlatives ('biggest, greatest, most powerful...') undermine enterprise authority and trigger reader skepticism.",
            guideline_reference="Tone & Voice: Authoritative, Transparent, and Professional",
            recommended_action="Replace",
            suggested_replacement="an advanced and highly capable enterprise platform",
            rationale="Replaces superlative marketing fluff with dignified, professional brand language."
        )

    buzzwords = [
        ("game-changer", "transformative governance platform", "Overused marketing jargon undermines enterprise credibility."),
        ("game-changing", "transformative", "Superlative jargon; prefer precise architectural description."),
        ("silver bullet", "comprehensive governance framework", "Cliche terminology dilutes technical authority."),
        ("magic bullet", "engineered solution", "Cliche terminology undermines professional brand tone."),
        ("proprietary AI engine", "ContentGuard Hybrid Governance Architecture", "Vague buzzword; use official branded architecture terminology."),
        ("secret sauce", "proprietary algorithmic validation", "Informal colloquialism inappropriate for enterprise communications."),
        ("industry-first", "advanced enterprise compliance", "Superlative claim; replace with descriptive capability."),
        ("revolutionary breakthrough", "significant innovation", "Hyperbolic tone conflicts with objective, factual brand voice standard."),
    ]

    for buzzword, fix, reason in buzzwords:
        pattern = re.compile(rf"(?i)\b{re.escape(buzzword)}\b")
        for match in pattern.finditer(content):
            add_finding(
                cat="brand_voice",
                module=IssueModule.BRAND_VOICE.value,
                severity=IssueSeverity.MEDIUM.value,
                issue_type="Brand Voice (Buzzword Drift)",
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=reason,
                guideline_reference="Brand Guidelines: Authoritative, Transparent, and Professional",
                recommended_action="Replace",
                suggested_replacement=fix,
                rationale=f"Enhances enterprise credibility by substituting '{buzzword}' with professional phrasing."
            )

    # Content Quality & Readability Advisory (Excessive Promotional Fluff & Cadence)
    # Detects high concentration of promotional superlatives and guarantees relative to factual feature descriptions.
    promotional_keywords = list(re.finditer(
        r"(?i)\b(?:best|greatest|amazing|revolutionary|most\s+powerful|most\s+advanced|10\s*times|\d+\s*times|guarantees?|perfect\s+results|never\s+need|only\s+platform|bulletproof|unhackable)\b",
        content
    ))
    words = content.split()
    if len(words) >= 20 and len(promotional_keywords) >= 4:
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
        if paragraphs:
            densest_p = max(
                paragraphs,
                key=lambda p: len(re.findall(r"(?i)\b(?:best|greatest|amazing|revolutionary|most\s+powerful|most\s+advanced|guarantees?|perfect)\b", p))
            )
            p_matches = len(re.findall(r"(?i)\b(?:best|greatest|amazing|revolutionary|most\s+powerful|most\s+advanced|guarantees?|perfect)\b", densest_p))
            if p_matches >= 3:
                p_start = content.find(densest_p)
                if p_start != -1:
                    add_finding(
                        cat="brand_voice",
                        module=IssueModule.BRAND_VOICE.value,
                        severity=IssueSeverity.LOW.value,
                        issue_type="Content Quality & Readability (Excessive Promotional Fluff)",
                        matched_text=densest_p,
                        start=p_start,
                        end=p_start + len(densest_p),
                        explanation=f"Excessive promotional fluff detected: paragraph contains {p_matches} hyperbolic claims in a short span. High marketing hype weakens readability and diminishes executive credibility.",
                        guideline_reference="Tone & Voice: Editorial Balance, Readability & Content Substance",
                        recommended_action="Review",
                        suggested_replacement="Substantiate promotional claims with verifiable use cases, benchmark metrics, or architectural capabilities.",
                        rationale="Balancing promotional assertions with concrete feature details elevates editorial readability."
                    )

    # Category / Format Specific Checks
    norm_category = (category or "").lower().strip()

    # Press Releases: Check for informal greetings / colloquial openings
    if norm_category in ["press_release", "official_communication"]:
        informal_openers = [
            ("Hey there", "FOR IMMEDIATE RELEASE", "Informal greeting inappropriate for an official press release."),
            ("Hey guys", "FOR IMMEDIATE RELEASE", "Casual colloquial opener violates corporate press release format."),
            ("Don't wait", "Organizations are encouraged to contact", "Direct consumer urgency language is unsuitable for corporate announcements.")
        ]
        for term, fix, explanation in informal_openers:
            for match in re.finditer(rf"(?i)\b{re.escape(term)}\b", content):
                add_finding(
                    cat="brand_voice",
                    module=IssueModule.BRAND_VOICE.value,
                    severity=IssueSeverity.MEDIUM.value,
                    issue_type="Format Standard (Press Release Tone)",
                    matched_text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    explanation=explanation,
                    guideline_reference="Brand Guidelines: Corporate Communications Standard",
                    recommended_action="Replace",
                    suggested_replacement=fix,
                    rationale="Aligns format with standard corporate news distribution protocols."
                )

    # Advertisements: Urgent aggressive sales pressure
    if norm_category in ["advertisement", "ad_copy", "paid_search"]:
        urgency_patterns = [
            ("Act now before it's too late", "Discover our enterprise solutions today", "Aggressive pressure tactic violates professional advertising standards."),
            ("Click here immediately", "Learn more about our governance platform", "Excessive urgency triggers ad network quality penalties.")
        ]
        for term, fix, explanation in urgency_patterns:
            for match in re.finditer(rf"(?i)\b{re.escape(term)}\b", content):
                add_finding(
                    cat="brand_voice",
                    module=IssueModule.MARKETING_CLAIM.value,
                    severity=IssueSeverity.LOW.value,
                    issue_type="Ad Compliance (High-Pressure Language)",
                    matched_text=match.group(),
                    start=match.start(),
                    end=match.end(),
                    explanation=explanation,
                    guideline_reference="Brand Guidelines: Paid Advertising Policy",
                    recommended_action="Replace",
                    suggested_replacement=fix,
                    rationale="Improves ad quality score and maintains dignified brand posture."
                )

    # Social Media: Twitter/X character length check
    if norm_category in ["social_media", "social_post"]:
        platform = (target_platform or "").lower()
        if "twitter" in platform or "x" in platform:
            if len(content) > 280:
                add_finding(
                    cat="brand_voice",
                    module=IssueModule.BRAND_VOICE.value,
                    severity=IssueSeverity.MEDIUM.value,
                    issue_type="Platform Limit (Character Count)",
                    matched_text=content[:30] + "...",
                    start=0,
                    end=min(30, len(content)),
                    explanation=f"Post length ({len(content)} characters) exceeds Twitter/X standard limit of 280 characters.",
                    guideline_reference="Channel Standards: Social Media Specifications",
                    recommended_action="Shorten",
                    suggested_replacement=None,
                    rationale="Shorten text to ensure the message renders without truncation."
                )

    # =========================================================================
    # 7. DYNAMIC DATABASE POLICIES (Restricted Terms & Approved Facts)
    # =========================================================================
    restricted_terms = db.query(RestrictedTerm).filter(
        RestrictedTerm.organization_id == organization_id,
        RestrictedTerm.is_active == True
    ).all()

    for rt in restricted_terms:
        term = rt.term.strip()
        escaped = re.escape(term)
        pattern = re.compile(rf"(?i)\b{escaped}\b")
        for match in pattern.finditer(content):
            add_finding(
                cat="brand_voice",
                module=IssueModule.RESTRICTED_LANGUAGE.value,
                severity=rt.severity,
                issue_type=f"Restricted Terminology ({rt.category.replace('_', ' ').title()})",
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=rt.reason,
                guideline_reference="Brand Knowledge Hub: Restricted Terminology Dictionary",
                recommended_action="Replace",
                suggested_replacement=rt.suggested_alternative,
                rationale=f"Replace prohibited term with officially approved alternative '{rt.suggested_alternative}'."
            )

    approved_facts = db.query(ApprovedFact).filter(
        ApprovedFact.organization_id == organization_id,
        ApprovedFact.is_active == True
    ).all()

    # Fact Check: Uptime / SLA Availability
    uptime_fact = next((f for f in approved_facts if "uptime" in f.statement.lower() or "sla" in f.topic.lower()), None)
    verified_uptime = 99.9
    if uptime_fact and uptime_fact.verified_numbers:
        verified_uptime = uptime_fact.verified_numbers.get("uptime_sla", 99.9)

    uptime_claims = list(re.finditer(r"(?i)\b(?:100%\s*(?:flawless\s*)?uptime|zero\s*downtime|99\.999%\s*uptime)\b", content))
    for match in uptime_claims:
        add_finding(
            cat="misleading_claim",
            module=IssueModule.FACT_CHECKER.value,
            severity=IssueSeverity.HIGH.value,
            issue_type="Factual Inconsistency (Uptime SLA)",
            matched_text=match.group(),
            start=match.start(),
            end=match.end(),
            explanation=f"Content promises '{match.group()}', but the official verified SLA in the Approved Facts Vault is {verified_uptime}% uptime backed by SOC-2.",
            guideline_reference="Approved Facts Vault: SLA & Availability",
            recommended_action="Replace",
            suggested_replacement=f"{verified_uptime}% uptime SLA",
            rationale=f"Aligns marketing statement with contractual SLA commitment ({verified_uptime}%)."
        )

    # Fact Check: Processing Throughput / Capacity
    throughput_fact = next((f for f in approved_facts if "throughput" in f.statement.lower() or "processing" in f.topic.lower() or "evaluations" in f.statement.lower()), None)
    verified_evals = 12000
    if throughput_fact and throughput_fact.verified_numbers:
        verified_evals = throughput_fact.verified_numbers.get("evals_per_min", 12000)

    for match in re.finditer(r"(?i)\b(\d{1,3}(?:,\d{3})+|\d+)\s*(?:documents|evaluations|records)\s*(?:per|\/)\s*(?:minute|min)\b", content):
        claimed_num_str = re.sub(r"[^\d]", "", match.group(1))
        claimed_num = int(claimed_num_str) if claimed_num_str else 0
        if claimed_num > int(verified_evals * 1.2):
            add_finding(
                cat="misleading_claim",
                module=IssueModule.FACT_CHECKER.value,
                severity=IssueSeverity.CRITICAL.value,
                issue_type="Factual Inconsistency (Processing Capacity)",
                matched_text=match.group(),
                start=match.start(),
                end=match.end(),
                explanation=f"Claimed throughput of {claimed_num:,} items/min conflicts with official verified capacity of {verified_evals:,} items/min.",
                guideline_reference="Approved Facts Vault: Processing Capacity",
                recommended_action="Replace",
                suggested_replacement=f"processes up to {verified_evals:,} evaluations per minute",
                rationale="Corrects unverified capacity metric to match officially audited system specifications."
            )

    # Sort all findings chronologically by character start offset
    findings.sort(key=lambda x: (x.get("char_start") or 0))
    logger.info(f"Deterministic scan finished: detected {len(findings)} issues across content.")
    return findings
