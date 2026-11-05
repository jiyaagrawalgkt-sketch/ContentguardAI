import sys
import os
import uuid
from datetime import date

# Ensure backend root is on Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.core.database import SessionLocal, init_db
from app.core.security import hash_password
from app.models import (
    Organization,
    User,
    UserRole,
    BrandGuideline,
    ApprovedFact,
    RestrictedTerm,
    BrandAsset,
    AuditLog,
)

DEMO_PASSWORD = "Demo@123"

DEMO_USERS = [
    {
        "email": "creator@contentguard.demo",
        "full_name": "Alex Rivera (Creator)",
        "role": UserRole.CREATOR.value,
        "password": DEMO_PASSWORD,
    },
    {
        "email": "reviewer@contentguard.demo",
        "full_name": "Samantha Chen (Reviewer)",
        "role": UserRole.REVIEWER.value,
        "password": DEMO_PASSWORD,
    },
    {
        "email": "admin@contentguard.demo",
        "full_name": "Marcus Vance (Admin)",
        "role": UserRole.ADMIN.value,
        "password": DEMO_PASSWORD,
    },
]


def seed_demo_environment(db=None):
    """Populates the database with Acme Corp guidelines, facts, restricted terms, and 3 demo personas."""
    close_session = False
    if db is None:
        init_db()
        db = SessionLocal()
        close_session = True

    try:
        # 1. Organization
        org = db.query(Organization).filter_by(slug="acme-global").first()
        if not org:
            org = Organization(
                id=str(uuid.uuid4()),
                name="Acme Global Technologies",
                slug="acme-global",
                industry="Enterprise Cloud Software"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
            print(f"Created organization: {org.name} ({org.id})")

        # 2. Demo Users
        for user_data in DEMO_USERS:
            existing = db.query(User).filter_by(email=user_data["email"]).first()
            if not existing:
                user = User(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    email=user_data["email"],
                    hashed_password=hash_password(user_data["password"]),
                    full_name=user_data["full_name"],
                    role=user_data["role"],
                    is_active=True
                )
                db.add(user)
                db.commit()
                print(f"Created demo user: {user.email} (Role: {user.role})")
            else:
                # Update password to ensure it matches DEMO_PASSWORD
                existing.hashed_password = hash_password(user_data["password"])
                db.commit()

        # 3. Brand Guidelines
        guidelines = [
            {
                "category": "tone_voice",
                "title": "Authoritative, Transparent, and Professional",
                "description": "All external communications must reflect technical credibility without hyperbole. Express confidence through facts rather than superlatives.",
                "rules": [
                    "Use active voice and direct statements",
                    "Avoid marketing buzzwords like 'game-changer' or 'silver bullet'",
                    "Never claim unverified market superiority"
                ],
                "severity_level": "high"
            },
            {
                "category": "policy",
                "title": "Zero Absolute Performance Guarantees",
                "description": "Never publish unqualified statements guaranteeing financial returns, 100% risk-free outcomes, or absolute timeline commitments without disclaimer.",
                "rules": [
                    "Prohibit phrases such as '100% risk-free' or 'guaranteed double returns'",
                    "All case study numbers must cite customer segment and date range"
                ],
                "severity_level": "critical"
            },
            {
                "category": "writing_rules",
                "title": "Clarity & Accessibility Standards",
                "description": "Maintain a target reading grade of 8th to 10th grade. Ensure all promotional copy contains clear calls to action and verifiable claims.",
                "rules": [
                    "Sentences should average under 25 words",
                    "Define technical acronyms on first mention"
                ],
                "severity_level": "medium"
            }
        ]

        for g in guidelines:
            if not db.query(BrandGuideline).filter_by(organization_id=org.id, title=g["title"]).first():
                guideline_obj = BrandGuideline(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    category=g["category"],
                    title=g["title"],
                    description=g["description"],
                    rules=g["rules"],
                    severity_level=g["severity_level"]
                )
                db.add(guideline_obj)

        # 4. Approved Facts Vault
        facts = [
            {
                "topic": "SLA & Availability",
                "statement": "ContentGuard AI provides a 99.9% uptime SLA backed by SOC-2 Type II certified enterprise infrastructure.",
                "verified_numbers": {"uptime_sla": 99.9, "cert": "SOC-2 Type II"},
                "reference_url_or_doc": "https://acme.com/trust/soc2-report.pdf"
            },
            {
                "topic": "Processing Capacity",
                "statement": "ContentGuard AI processes up to 12,000 compliance document evaluations per minute with sub-500ms latency.",
                "verified_numbers": {"evals_per_min": 12000, "latency_ms": 500},
                "reference_url_or_doc": "https://acme.com/benchmarks/2026-throughput"
            },
            {
                "topic": "Supported Formats",
                "statement": "ContentGuard AI natively parses PDF, DOCX, TXT, PNG, and JPG documents with full OCR extraction.",
                "verified_numbers": {"format_count": 5},
                "reference_url_or_doc": "Acme Product Specs v4.2"
            }
        ]

        for f in facts:
            if not db.query(ApprovedFact).filter_by(organization_id=org.id, topic=f["topic"]).first():
                fact_obj = ApprovedFact(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    topic=f["topic"],
                    statement=f["statement"],
                    verified_numbers=f["verified_numbers"],
                    reference_url_or_doc=f["reference_url_or_doc"],
                    effective_date=date.today()
                )
                db.add(fact_obj)

        # 5. Restricted Terminology Dictionary
        restricted_terms = [
            {
                "term": "100% risk-free guarantee",
                "category": "prohibited",
                "severity": "critical",
                "suggested_alternative": "enterprise-grade reliability assurance",
                "reason": "Violates marketing policy prohibiting absolute financial and operational guarantees."
            },
            {
                "term": "proprietary AI engine",
                "category": "unapproved_superlative",
                "severity": "medium",
                "suggested_alternative": "ContentGuard Hybrid Governance Architecture",
                "reason": "Vague buzzword; use official branded architecture terminology."
            },
            {
                "term": "no other competitor can match",
                "category": "misleading_claim",
                "severity": "high",
                "suggested_alternative": "designed to outperform legacy manual workflows",
                "reason": "Unsupported superiority claim; exposes organization to legal challenge without comparative study."
            },
            {
                "term": "double your leads",
                "category": "unapproved_superlative",
                "severity": "high",
                "suggested_alternative": "measurably improve conversion efficiency",
                "reason": "Unqualified multiplier claim not backed by verified universal customer statistics."
            }
        ]

        for rt in restricted_terms:
            if not db.query(RestrictedTerm).filter_by(organization_id=org.id, term=rt["term"]).first():
                term_obj = RestrictedTerm(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    term=rt["term"],
                    category=rt["category"],
                    severity=rt["severity"],
                    suggested_alternative=rt["suggested_alternative"],
                    reason=rt["reason"]
                )
                db.add(term_obj)

        # 6. Brand Assets & Visual Palette
        assets = [
            {
                "name": "Acme Brand Color Palette",
                "asset_type": "color_palette",
                "primary_color_hex": "#0B0F19",
                "secondary_color_hex": "#6366F1",
                "accent_color_hex": "#FAF9FF",
                "rules_json": {
                    "contrast_ratio_min": 4.5,
                    "max_accent_coverage_percent": 20
                }
            },
            {
                "name": "Official Primary Logo",
                "asset_type": "logo",
                "file_path": "/assets/logos/acme_primary.svg",
                "rules_json": {
                    "min_clear_space_px": 24,
                    "min_width_px": 120
                }
            }
        ]

        for a in assets:
            if not db.query(BrandAsset).filter_by(organization_id=org.id, name=a["name"]).first():
                asset_obj = BrandAsset(
                    id=str(uuid.uuid4()),
                    organization_id=org.id,
                    name=a["name"],
                    asset_type=a["asset_type"],
                    primary_color_hex=a.get("primary_color_hex"),
                    secondary_color_hex=a.get("secondary_color_hex"),
                    accent_color_hex=a.get("accent_color_hex"),
                    file_path=a.get("file_path"),
                    rules_json=a.get("rules_json")
                )
                db.add(asset_obj)

        db.commit()
        print("Demo seed completed successfully!")

    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    seed_demo_environment()
