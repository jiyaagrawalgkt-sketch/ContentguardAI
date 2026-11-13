from sqlalchemy import create_engine, event, text as sa_text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

from pathlib import Path

# Configure database URL (handle Render/Heroku 'postgres://' compatibility)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)
elif db_url.startswith("sqlite"):
    # Ensure SQLite URL points to canonical absolute database file path
    # Regardless of whether process was launched from repo root or backend/ folder
    raw_path = db_url.replace("sqlite:///", "")
    clean_path = raw_path.lstrip("./")
    cwd = Path.cwd()
    if (cwd / "backend" / "contentguard.db").exists():
        canon = (cwd / "backend" / "contentguard.db").resolve()
    elif (cwd / "contentguard.db").exists():
        canon = (cwd / "contentguard.db").resolve()
    else:
        canon = (Path(__file__).resolve().parent.parent.parent / "contentguard.db")
    db_url = f"sqlite:///{canon.as_posix()}"

# Configure SQLite or PostgreSQL connection arguments
connect_args = {}
if db_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    db_url,
    connect_args=connect_args,
    pool_pre_ping=True
)

# Enforce foreign key constraints in SQLite for complete relational integrity
@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if db_url.startswith("sqlite"):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """Dependency to provide a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables in the database if they do not exist and ensure schema parity."""
    # Import all models to ensure metadata is fully populated
    import app.models  # noqa
    Base.metadata.create_all(bind=engine)

    # Safe migration for new enterprise compliance columns
    try:
        with engine.begin() as conn:
            if db_url.startswith("sqlite"):
                cursor = conn.connection.cursor()
                
                # detected_issues
                cursor.execute("PRAGMA table_info(detected_issues)")
                existing_cols = {row[1] for row in cursor.fetchall()}
                if existing_cols:
                    if "category" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN category VARCHAR(50) DEFAULT 'brand_voice'"))
                    if "recommended_action" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN recommended_action VARCHAR(30) DEFAULT 'Replace'"))
                    if "correction_type" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN correction_type VARCHAR(30) DEFAULT 'REPLACE'"))
                    if "suggested_replacement" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN suggested_replacement TEXT"))
                    if "detection_source" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN detection_source VARCHAR(50) DEFAULT 'Rule Engine'"))
                    if "is_dismissed" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN is_dismissed BOOLEAN DEFAULT 0"))
                    if "dismiss_reason" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN dismiss_reason VARCHAR(255)"))

                # users
                cursor.execute("PRAGMA table_info(users)")
                user_cols = {row[1] for row in cursor.fetchall()}
                if user_cols:
                    if "mfa_enabled" not in user_cols:
                        conn.execute(sa_text("ALTER TABLE users ADD COLUMN mfa_enabled BOOLEAN DEFAULT 0"))
                    if "mfa_secret" not in user_cols:
                        conn.execute(sa_text("ALTER TABLE users ADD COLUMN mfa_secret VARCHAR(64)"))

                # brand_assets
                cursor.execute("PRAGMA table_info(brand_assets)")
                asset_cols = {row[1] for row in cursor.fetchall()}
                if asset_cols:
                    if "neutral_color_hex" not in asset_cols:
                        conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN neutral_color_hex VARCHAR(7)"))
                    if "color_palette_json" not in asset_cols:
                        conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN color_palette_json JSON"))
                    if "logo_hash" not in asset_cols:
                        conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN logo_hash VARCHAR(128)"))
                    if "wcag_min_contrast" not in asset_cols:
                        conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN wcag_min_contrast FLOAT DEFAULT 4.5"))

                # extracted_claims
                cursor.execute("PRAGMA table_info(extracted_claims)")
                claim_cols = {row[1] for row in cursor.fetchall()}
                if claim_cols:
                    if "sentence" not in claim_cols:
                        conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN sentence TEXT"))
                    if "claim_category" not in claim_cols:
                        conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN claim_category VARCHAR(50)"))
                    if "analysis_version" not in claim_cols:
                        conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN analysis_version INTEGER DEFAULT 1"))
                    if "analyzed_at" not in claim_cols:
                        conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN analyzed_at DATETIME"))
                cursor.close()
            else:
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'brand_voice'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS recommended_action VARCHAR(30) DEFAULT 'Replace'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS correction_type VARCHAR(30) DEFAULT 'REPLACE'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS suggested_replacement TEXT"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS detection_source VARCHAR(50) DEFAULT 'Rule Engine'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS is_dismissed BOOLEAN DEFAULT FALSE"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS dismiss_reason VARCHAR(255)"))
                conn.execute(sa_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_enabled BOOLEAN DEFAULT FALSE"))
                conn.execute(sa_text("ALTER TABLE users ADD COLUMN IF NOT EXISTS mfa_secret VARCHAR(64)"))
                conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN IF NOT EXISTS neutral_color_hex VARCHAR(7)"))
                conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN IF NOT EXISTS sentence TEXT"))
                conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN IF NOT EXISTS claim_category VARCHAR(50)"))
                conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN IF NOT EXISTS analysis_version INTEGER DEFAULT 1"))
                conn.execute(sa_text("ALTER TABLE extracted_claims ADD COLUMN IF NOT EXISTS analyzed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
                conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN IF NOT EXISTS color_palette_json JSONB"))
                conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN IF NOT EXISTS logo_hash VARCHAR(128)"))
                conn.execute(sa_text("ALTER TABLE brand_assets ADD COLUMN IF NOT EXISTS wcag_min_contrast FLOAT DEFAULT 4.5"))
    except Exception:
        pass
    except Exception:
        pass
