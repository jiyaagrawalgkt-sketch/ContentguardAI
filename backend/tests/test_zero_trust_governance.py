import pytest
import uuid
from app.core.security import (
    validate_password_complexity,
    create_access_token,
    create_refresh_token,
    decode_access_token,
    decode_refresh_token,
    generate_totp_secret,
    get_totp_uri,
    verify_totp,
)
from app.models.user import User, UserRole, RefreshToken
from app.models.organization import Organization
from app.models.audit import AuditLog
from app.api.v1.endpoints.auth import (
    register,
    login,
    refresh_token_endpoint,
    logout,
    _hash_token,
    google_login,
    demo_login,
)
from app.api.v1.endpoints.brand_knowledge import (
    create_or_update_brand_asset,
    list_brand_assets,
)
from app.schemas.auth import (
    UserRegister,
    UserLogin,
    RefreshTokenRequest,
    GoogleLoginRequest,
    DemoLoginRequest,
)


def test_password_complexity_rules():
    """Verify password rules reject weak passwords and accept complex ones."""
    # Too short
    ok, reason = validate_password_complexity("Short1!")
    assert not ok
    assert "at least 8 characters" in reason

    # No uppercase
    ok, reason = validate_password_complexity("alllowercase123!")
    assert not ok
    assert "uppercase" in reason

    # No number
    ok, reason = validate_password_complexity("NoNumbersHere!")
    assert not ok
    assert "digit" in reason

    # No special character
    ok, reason = validate_password_complexity("NoSpecialChar123")
    assert not ok
    assert "special character" in reason

    # Valid complex password
    ok, reason = validate_password_complexity("Enterprise#2026Secure")
    assert ok


def test_refresh_token_lifecycle(db):
    """Verify refresh token issuance, rotation, and revocation."""
    org = Organization(id=str(uuid.uuid4()), name="ZeroTrust Org", slug=f"zt-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.commit()

    reg_data = UserRegister(
        email=f"zt_{uuid.uuid4().hex[:6]}@contentguard.test",
        password="ValidPassword@123",
        full_name="Zero Trust User",
        role="creator",
        organization_name=org.name
    )
    reg_res = register(user_in=reg_data, db=db)
    assert reg_res.access_token is not None
    assert reg_res.refresh_token is not None

    # Rotate refresh token
    rotate_res = refresh_token_endpoint(
        req=RefreshTokenRequest(refresh_token=reg_res.refresh_token),
        db=db
    )
    assert rotate_res.access_token is not None
    assert rotate_res.refresh_token != reg_res.refresh_token

    # Reusing the old revoked refresh token must be rejected
    with pytest.raises(Exception):
        refresh_token_endpoint(
            req=RefreshTokenRequest(refresh_token=reg_res.refresh_token),
            db=db
        )


def test_mfa_totp_generation_and_verification():
    """Test TOTP secret generation, provisioning URI, and verification window."""
    import pyotp

    secret = generate_totp_secret()
    assert len(secret) >= 16

    uri = get_totp_uri(secret, "user@test.org", issuer_name="ContentGuard AI")
    assert "otpauth://totp/" in uri
    assert "ContentGuard" in uri

    # Generate current TOTP code and verify
    totp = pyotp.TOTP(secret)
    current_code = totp.now()

    assert verify_totp(secret, current_code) is True
    assert verify_totp(secret, "000000") is False
    assert verify_totp("", current_code) is False


def test_compliance_officer_audit_access(db):
    """Verify append-only audit records exist and link to organization."""
    org = Organization(id=str(uuid.uuid4()), name="Audit Org", slug=f"audit-{uuid.uuid4().hex[:6]}")
    db.add(org)
    db.commit()

    audit_entry = AuditLog(
        organization_id=org.id,
        action="TEST_SECURITY_ACTION",
        entity_type="system",
        entity_id=str(uuid.uuid4()),
        details={"ip": "127.0.0.1", "status": "verified"}
    )
    db.add(audit_entry)
    db.commit()

    found = db.query(AuditLog).filter(
        AuditLog.organization_id == org.id,
        AuditLog.action == "TEST_SECURITY_ACTION"
    ).first()
    assert found is not None
    assert found.details["status"] == "verified"


def test_judge_demo_account_authentication(db):
    """Verify that Judge Demo account authenticates and yields valid tokens."""
    res = demo_login(req=DemoLoginRequest(role="demo"), db=db)
    assert res.access_token is not None
    assert res.refresh_token is not None
    assert res.user.email == "demo@contentguard.ai"
    assert res.user.role == "creator"


def test_google_login_flow(db):
    """Verify Google OAuth token verification, user provisioning, and session tokens."""
    test_email = f"judge_{uuid.uuid4().hex[:6]}@contentguard.ai"
    req = GoogleLoginRequest(credential=f"test_google_token_{test_email}")
    res = google_login(req=req, db=db)
    assert res.access_token is not None
    assert res.refresh_token is not None
    assert res.user.email == test_email
    assert res.user.role == "creator"


def test_brand_assets_crud(db):
    """Verify brand asset creation, color palette management, and organization isolation."""
    org = Organization(id=str(uuid.uuid4()), name="Asset Org", slug=f"asset-{uuid.uuid4().hex[:6]}")
    admin_user = User(
        id=str(uuid.uuid4()),
        organization_id=org.id,
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        hashed_password="hash",
        full_name="Asset Admin",
        role=UserRole.ADMIN.value,
        is_active=True
    )
    db.add_all([org, admin_user])
    db.commit()

    asset_data = {
        "name": "Corporate Master Palette",
        "asset_type": "color_palette",
        "primary_color_hex": "#0B0F19",
        "secondary_color_hex": "#6366F1",
        "neutral_color_hex": "#FFFFFF",
        "color_palette_json": ["#0B0F19", "#6366F1", "#FFFFFF"],
        "wcag_min_contrast": 4.5
    }

    created = create_or_update_brand_asset(payload=asset_data, current_user=admin_user, db=db)
    assert created["id"] is not None
    assert created["name"] == "Corporate Master Palette"

    assets = list_brand_assets(current_user=admin_user, db=db)
    assert len(assets) >= 1
    assert any(a["name"] == "Corporate Master Palette" for a in assets)

