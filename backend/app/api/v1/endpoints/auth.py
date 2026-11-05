import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.core.permissions import get_current_user
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.audit import AuditLog
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    DemoLoginRequest,
    UserOut,
    Token,
)
from scripts.seed_demo import seed_demo_environment

from sqlalchemy import func

router = APIRouter()


def _format_user_out(user: User) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        is_active=user.is_active,
        created_at=user.created_at,
    )


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED, summary="Register User")
def register(user_in: UserRegister, db: Session = Depends(get_db)):
    """Register a new user and assign to an organization."""
    email_clean = user_in.email.strip().lower()
    existing_user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists"
        )

    # Resolve or create organization with strict isolation
    if user_in.organization_name and user_in.organization_name.strip():
        org_name = user_in.organization_name.strip()
        slug = org_name.lower().replace(" ", "-")
        org = db.query(Organization).filter(Organization.slug == slug).first()
        if not org:
            org = Organization(
                id=str(uuid.uuid4()),
                name=org_name,
                slug=slug,
                industry="Software & Marketing"
            )
            db.add(org)
            db.commit()
            db.refresh(org)
    else:
        # Isolated personal workspace for standalone registrations
        unique_suffix = uuid.uuid4().hex[:8]
        org_name = f"{user_in.full_name.strip()}'s Workspace"
        slug = f"ws-{unique_suffix}"
        org = Organization(
            id=str(uuid.uuid4()),
            name=org_name,
            slug=slug,
            industry="Software & Marketing"
        )
        db.add(org)
        db.commit()
        db.refresh(org)

    # Validate role
    role = user_in.role or UserRole.CREATOR.value
    if role not in [r.value for r in UserRole]:
        role = UserRole.CREATOR.value

    user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=email_clean,
        hashed_password=hash_password(user_in.password),
        full_name=user_in.full_name.strip(),
        role=role,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Record audit log
    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action="AUTH_REGISTER",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email, "role": user.role}
    )
    db.add(audit)
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        organization_id=user.organization_id,
        email=user.email
    )

    return Token(access_token=token, token_type="bearer", user=_format_user_out(user))


@router.post("/login", response_model=Token, summary="User Login")
def login(login_data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email and password and return a JWT access token."""
    email_clean = login_data.email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is deactivated"
        )

    # Record login audit
    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=user.id,
        action="AUTH_LOGIN",
        entity_type="user",
        entity_id=user.id,
        details={"email": user.email}
    )
    db.add(audit)
    db.commit()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        organization_id=user.organization_id,
        email=user.email
    )

    return Token(access_token=token, token_type="bearer", user=_format_user_out(user))


@router.get("/me", response_model=UserOut, summary="Get Current Authenticated User")
def get_me(current_user: User = Depends(get_current_user)):
    """Returns the authenticated user's profile and active organization."""
    return _format_user_out(current_user)


@router.post("/demo-login", response_model=Token, summary="Quick Demo Persona Login")
def demo_login(req: DemoLoginRequest, db: Session = Depends(get_db)):
    """
    Instant 1-click persona switcher for product evaluation and role-based tours.
    Supports roles: 'creator', 'reviewer', 'admin'.
    """
    role_requested = req.role.lower().strip()
    email_map = {
        "creator": "creator@contentguard.demo",
        "reviewer": "reviewer@contentguard.demo",
        "admin": "admin@contentguard.demo",
    }

    if role_requested not in email_map:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo role. Allowed roles are: {', '.join(email_map.keys())}"
        )

    target_email = email_map[role_requested]
    user = db.query(User).filter(User.email == target_email).first()

    # If demo accounts haven't been seeded yet, auto-seed them now
    if not user:
        seed_demo_environment(db=db)
        user = db.query(User).filter(User.email == target_email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Demo environment could not be initialized"
        )

    token = create_access_token(
        subject=user.id,
        role=user.role,
        organization_id=user.organization_id,
        email=user.email
    )

    return Token(access_token=token, token_type="bearer", user=_format_user_out(user))


@router.get("/demo-accounts", summary="List Available Demo Accounts")
def list_demo_accounts():
    """Returns public metadata of the pre-seeded demo accounts for quick role-based evaluation."""
    return [
        {
            "role": "creator",
            "email": "creator@contentguard.demo",
            "name": "Alex Rivera",
            "title": "Senior Content Creator",
            "description": "Upload drafts, run AI analysis, review findings, and accept suggested fixes."
        },
        {
            "role": "reviewer",
            "email": "reviewer@contentguard.demo",
            "name": "Samantha Chen",
            "title": "Brand Governance Reviewer",
            "description": "Inspect submissions, view side-by-side diffs, request changes, and approve."
        },
        {
            "role": "admin",
            "email": "admin@contentguard.demo",
            "name": "Marcus Vance",
            "title": "Organization Administrator",
            "description": "Configure brand voice guidelines, manage approved facts, restricted terms, and view audit trail."
        }
    ]
