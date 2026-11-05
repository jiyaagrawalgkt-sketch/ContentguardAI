import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.core.database import get_db, engine
from app.core.security import hash_password
from app.core.permissions import require_admin
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.models.submission import ContentSubmission, SubmissionStatus
from app.models.analysis import AnalysisReport
from app.models.audit import AuditLog
from app.models.brand_knowledge import BrandGuideline
from app.schemas.admin import (
    AdminOverviewOut,
    AdminUserOut,
    AdminUserCreate,
    AdminUserRoleUpdate,
    AdminUserStatusUpdate,
    AdminOrgOut,
    AdminOrgCreate,
    AdminActivityItem,
    AdminSystemHealth
)

router = APIRouter()


# -------------------------------------------------------------
# 1. Admin Overview
# -------------------------------------------------------------
@router.get("/overview", response_model=AdminOverviewOut, summary="Get Platform Overview Statistics")
def get_admin_overview(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns platform-wide aggregate metrics computed from actual database records.
    """
    total_users = db.query(func.count(User.id)).scalar() or 0
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    total_submissions = db.query(func.count(ContentSubmission.id)).scalar() or 0

    pending_reviews = db.query(func.count(ContentSubmission.id)).filter(
        ContentSubmission.status == SubmissionStatus.PENDING_REVIEW.value
    ).scalar() or 0

    approved_publications = db.query(func.count(ContentSubmission.id)).filter(
        ContentSubmission.status.in_([
            SubmissionStatus.APPROVED.value,
            SubmissionStatus.PUBLISHED.value
        ])
    ).scalar() or 0

    rejected_submissions = db.query(func.count(ContentSubmission.id)).filter(
        ContentSubmission.status == SubmissionStatus.REJECTED.value
    ).scalar() or 0

    avg_score = db.query(func.avg(AnalysisReport.compliance_score)).scalar()
    avg_compliance = round(float(avg_score), 1) if avg_score is not None else 100.0

    return AdminOverviewOut(
        total_users=total_users,
        total_organizations=total_orgs,
        total_submissions=total_submissions,
        pending_reviews=pending_reviews,
        approved_publications=approved_publications,
        rejected_submissions=rejected_submissions,
        average_compliance_score=avg_compliance
    )


# -------------------------------------------------------------
# 2. User Management
# -------------------------------------------------------------
@router.get("/users", response_model=List[AdminUserOut], summary="List All Users")
def list_admin_users(
    search: Optional[str] = Query(None, description="Search by name or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns all registered users with their organization association and status.
    """
    query = db.query(User)
    if search:
        search_fmt = f"%{search.strip().lower()}%"
        query = query.filter(
            (func.lower(User.email).like(search_fmt)) |
            (func.lower(User.full_name).like(search_fmt))
        )
    if role:
        query = query.filter(User.role == role.lower().strip())

    users = query.order_by(desc(User.created_at)).all()

    return [
        AdminUserOut(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            role=u.role,
            organization_id=u.organization_id,
            organization_name=u.organization.name if u.organization else "None",
            is_active=u.is_active,
            created_at=u.created_at
        )
        for u in users
    ]


@router.post("/users", response_model=AdminUserOut, status_code=status.HTTP_201_CREATED, summary="Create User")
def create_admin_user(
    payload: AdminUserCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Admin creates a user directly and assigns an organization and role.
    """
    email_clean = payload.email.strip().lower()
    existing = db.query(User).filter(func.lower(User.email) == email_clean).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    # Resolve organization
    org = None
    if payload.organization_id:
        org = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    elif payload.organization_name:
        slug = payload.organization_name.lower().strip().replace(" ", "-")
        org = db.query(Organization).filter(Organization.slug == slug).first()
        if not org:
            org = Organization(id=str(uuid.uuid4()), name=payload.organization_name, slug=slug)
            db.add(org)
            db.commit()
            db.refresh(org)
    else:
        org = current_user.organization

    if not org:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Valid organization required")

    role_val = payload.role.lower().strip()
    if role_val not in [r.value for r in UserRole]:
        role_val = UserRole.CREATOR.value

    new_user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=email_clean,
        hashed_password=hash_password(payload.password),
        full_name=payload.full_name.strip(),
        role=role_val,
        is_active=True
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    audit = AuditLog(
        organization_id=org.id,
        user_id=current_user.id,
        action="ADMIN_CREATE_USER",
        entity_type="user",
        entity_id=new_user.id,
        details={"created_email": new_user.email, "role": new_user.role}
    )
    db.add(audit)
    db.commit()

    return AdminUserOut(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name,
        role=new_user.role,
        organization_id=new_user.organization_id,
        organization_name=org.name,
        is_active=new_user.is_active,
        created_at=new_user.created_at
    )


@router.put("/users/{user_id}/role", response_model=AdminUserOut, summary="Update User Role")
def update_user_role(
    user_id: str,
    payload: AdminUserRoleUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Updates the role of a user (creator, reviewer, admin).
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role_val = payload.role.lower().strip()
    if role_val not in [r.value for r in UserRole]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid role specified")

    user.role = role_val
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=current_user.id,
        action="ADMIN_UPDATE_ROLE",
        entity_type="user",
        entity_id=user.id,
        details={"new_role": user.role}
    )
    db.add(audit)
    db.commit()

    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        is_active=user.is_active,
        created_at=user.created_at
    )


@router.put("/users/{user_id}/status", response_model=AdminUserOut, summary="Activate or Deactivate User")
def toggle_user_status(
    user_id: str,
    payload: AdminUserStatusUpdate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Activates or deactivates an account. An admin cannot deactivate themselves.
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Administrators cannot deactivate their own account"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = payload.is_active
    db.commit()
    db.refresh(user)

    audit = AuditLog(
        organization_id=user.organization_id,
        user_id=current_user.id,
        action="ADMIN_TOGGLE_USER_STATUS",
        entity_type="user",
        entity_id=user.id,
        details={"is_active": user.is_active}
    )
    db.add(audit)
    db.commit()

    return AdminUserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=user.organization.name if user.organization else None,
        is_active=user.is_active,
        created_at=user.created_at
    )


# -------------------------------------------------------------
# 3. Organization Management
# -------------------------------------------------------------
@router.get("/organizations", response_model=List[AdminOrgOut], summary="List All Organizations")
def list_admin_organizations(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns all organizations with counts of active members, submissions, and brand rules.
    """
    orgs = db.query(Organization).order_by(desc(Organization.created_at)).all()
    results = []
    for org in orgs:
        u_count = len(org.users)
        s_count = len(org.submissions)
        g_count = len(org.brand_guidelines)
        results.append(
            AdminOrgOut(
                id=org.id,
                name=org.name,
                slug=org.slug,
                industry=org.industry,
                user_count=u_count,
                submission_count=s_count,
                guidelines_count=g_count,
                created_at=org.created_at
            )
        )
    return results


@router.post("/organizations", response_model=AdminOrgOut, status_code=status.HTTP_201_CREATED, summary="Create Organization")
def create_admin_organization(
    payload: AdminOrgCreate,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Creates a new organization tenant.
    """
    slug = payload.name.lower().strip().replace(" ", "-")
    existing = db.query(Organization).filter(Organization.slug == slug).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="An organization with this name already exists")

    new_org = Organization(
        id=str(uuid.uuid4()),
        name=payload.name.strip(),
        slug=slug,
        industry=payload.industry or "Enterprise Cloud Software"
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    audit = AuditLog(
        organization_id=new_org.id,
        user_id=current_user.id,
        action="ADMIN_CREATE_ORG",
        entity_type="organization",
        entity_id=new_org.id,
        details={"name": new_org.name, "slug": new_org.slug}
    )
    db.add(audit)
    db.commit()

    return AdminOrgOut(
        id=new_org.id,
        name=new_org.name,
        slug=new_org.slug,
        industry=new_org.industry,
        user_count=0,
        submission_count=0,
        guidelines_count=0,
        created_at=new_org.created_at
    )


# -------------------------------------------------------------
# 4. System Monitoring & Audit Logs
# -------------------------------------------------------------
@router.get("/system/activity", response_model=List[AdminActivityItem], summary="Get System Activity Logs")
def get_system_activity(
    limit: int = Query(25, ge=5, le=100),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns the real recent audit activity across the entire platform.
    """
    logs = db.query(AuditLog).order_by(desc(AuditLog.created_at)).limit(limit).all()
    results = []
    for log in logs:
        results.append(
            AdminActivityItem(
                id=log.id,
                action=log.action,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                user_email=log.user.email if log.user else None,
                user_name=log.user.full_name if log.user else "System",
                details=log.details,
                created_at=log.created_at
            )
        )
    return results


@router.get("/system/health", response_model=AdminSystemHealth, summary="Get Live System Health")
def get_system_health(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """
    Returns actual database status and record counts.
    """
    db_type = "PostgreSQL" if "postgresql" in str(engine.url) else "SQLite"

    counts = {
        "users": db.query(func.count(User.id)).scalar() or 0,
        "organizations": db.query(func.count(Organization.id)).scalar() or 0,
        "submissions": db.query(func.count(ContentSubmission.id)).scalar() or 0,
        "reports": db.query(func.count(AnalysisReport.id)).scalar() or 0,
        "audit_logs": db.query(func.count(AuditLog.id)).scalar() or 0,
    }

    return AdminSystemHealth(
        database_connected=True,
        database_type=db_type,
        total_records=counts,
        environment="production",
        version="1.0.0"
    )
