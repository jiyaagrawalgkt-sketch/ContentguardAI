import pytest
from fastapi import HTTPException
from app.models.organization import Organization
from app.models.user import User, UserRole
from app.models.submission import ContentSubmission, SubmissionStatus
from app.core.security import hash_password
from app.schemas.admin import AdminUserCreate, AdminUserRoleUpdate, AdminUserStatusUpdate, AdminOrgCreate
from app.api.v1.endpoints.admin import (
    get_admin_overview,
    list_admin_users,
    create_admin_user,
    update_user_role,
    toggle_user_status,
    list_admin_organizations,
    create_admin_organization,
    get_system_health,
    get_system_activity
)


def test_admin_overview_stats(db):
    """Verify admin overview calculates real database counts."""
    org = Organization(id="org-adm", name="Admin Corp", slug="admin-corp")
    db.add(org)

    admin = User(
        id="usr-adm",
        organization_id=org.id,
        email="admin@contentguard.test",
        hashed_password=hash_password("AdminPass123!"),
        full_name="System Administrator",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    creator = User(
        id="usr-c1",
        organization_id=org.id,
        email="creator1@contentguard.test",
        hashed_password=hash_password("CreatorPass123!"),
        full_name="Creator One",
        role=UserRole.CREATOR.value,
        is_active=True
    )
    db.add_all([admin, creator])

    sub = ContentSubmission(
        id="sub-1",
        organization_id=org.id,
        creator_id=creator.id,
        title="Admin Test Post",
        category="marketing_email",
        status=SubmissionStatus.PENDING_REVIEW.value
    )
    db.add(sub)
    db.commit()

    overview = get_admin_overview(current_user=admin, db=db)
    assert overview.total_users == 2
    assert overview.total_organizations == 1
    assert overview.total_submissions == 1
    assert overview.pending_reviews == 1
    assert overview.approved_publications == 0
    assert overview.rejected_submissions == 0


def test_admin_user_management_crud(db):
    """Verify admin can list users, create users, update role and toggle active status."""
    org = Organization(id="org-adm-2", name="Ops Corp", slug="ops-corp")
    db.add(org)

    admin = User(
        id="usr-adm-2",
        organization_id=org.id,
        email="admin2@contentguard.test",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Ops Admin",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db.add(admin)
    db.commit()

    # 1. Create User
    new_user_req = AdminUserCreate(
        email="newuser@contentguard.test",
        password="SecurePassword123!",
        full_name="New Creator",
        role="creator",
        organization_id=org.id
    )
    created = create_admin_user(payload=new_user_req, current_user=admin, db=db)
    assert created.email == "newuser@contentguard.test"
    assert created.role == "creator"

    # 2. List Users with filter
    user_list = list_admin_users(search="newuser", role="creator", current_user=admin, db=db)
    assert len(user_list) == 1
    assert user_list[0].email == "newuser@contentguard.test"

    # 3. Update Role
    role_update = AdminUserRoleUpdate(role="reviewer")
    updated = update_user_role(user_id=created.id, payload=role_update, current_user=admin, db=db)
    assert updated.role == "reviewer"

    # 4. Toggle Status (Deactivate)
    status_update = AdminUserStatusUpdate(is_active=False)
    deactivated = toggle_user_status(user_id=created.id, payload=status_update, current_user=admin, db=db)
    assert deactivated.is_active is False

    # 5. Prevent Self-Deactivation
    with pytest.raises(HTTPException) as exc_info:
        toggle_user_status(user_id=admin.id, payload=status_update, current_user=admin, db=db)
    assert exc_info.value.status_code == 400


def test_admin_organization_management(db):
    """Verify admin can list and create organizations."""
    org = Organization(id="org-adm-3", name="Original Org", slug="original-org")
    db.add(org)
    admin = User(
        id="usr-adm-3",
        organization_id=org.id,
        email="admin3@contentguard.test",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Enterprise Admin",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db.add(admin)
    db.commit()

    # Create new org
    new_org_req = AdminOrgCreate(name="NextGen Global", industry="Cybersecurity")
    new_org = create_admin_organization(payload=new_org_req, current_user=admin, db=db)
    assert new_org.name == "NextGen Global"
    assert new_org.slug == "nextgen-global"

    # List orgs
    all_orgs = list_admin_organizations(current_user=admin, db=db)
    assert len(all_orgs) == 2


def test_admin_system_monitoring(db):
    """Verify live system health and activity audit logs."""
    org = Organization(id="org-health", name="Health Org", slug="health-org")
    db.add(org)
    admin = User(
        id="usr-adm-4",
        organization_id=org.id,
        email="admin4@contentguard.test",
        hashed_password=hash_password("AdminPass123!"),
        full_name="Monitoring Admin",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db.add(admin)
    db.commit()

    health = get_system_health(current_user=admin, db=db)
    assert health.database_connected is True
    assert health.total_records["users"] >= 1

    activity = get_system_activity(limit=10, current_user=admin, db=db)
    assert isinstance(activity, list)
