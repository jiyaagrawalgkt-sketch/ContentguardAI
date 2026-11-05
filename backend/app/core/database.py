from sqlalchemy import create_engine, event, text as sa_text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

# Configure database URL (handle Render/Heroku 'postgres://' compatibility)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

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
                cursor.execute("PRAGMA table_info(detected_issues)")
                existing_cols = {row[1] for row in cursor.fetchall()}
                cursor.close()
                if existing_cols:
                    if "category" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN category VARCHAR(50) DEFAULT 'brand_voice'"))
                    if "recommended_action" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN recommended_action VARCHAR(30) DEFAULT 'Replace'"))
                    if "detection_source" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN detection_source VARCHAR(50) DEFAULT 'Rule Engine'"))
                    if "is_dismissed" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN is_dismissed BOOLEAN DEFAULT 0"))
                    if "dismiss_reason" not in existing_cols:
                        conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN dismiss_reason VARCHAR(255)"))
            else:
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'brand_voice'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS recommended_action VARCHAR(30) DEFAULT 'Replace'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS detection_source VARCHAR(50) DEFAULT 'Rule Engine'"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS is_dismissed BOOLEAN DEFAULT FALSE"))
                conn.execute(sa_text("ALTER TABLE detected_issues ADD COLUMN IF NOT EXISTS dismiss_reason VARCHAR(255)"))
    except Exception:
        pass
