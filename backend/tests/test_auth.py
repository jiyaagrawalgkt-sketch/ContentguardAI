import pytest
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.database import Base
from app.core.security import hash_password, verify_password, create_access_token, decode_access_token
from app.core.permissions import RoleChecker
from app.models.user import User, UserRole
from app.models.organization import Organization
from app.schemas.auth import UserRegister, UserLogin, DemoLoginRequest
from app.api.v1.endpoints.auth import register, login, demo_login


@pytest.fixture(scope="function")
def db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    with engine.connect() as conn:
        conn.execute(text("PRAGMA foreign_keys=ON"))

    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSession()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def test_password_hashing():
    pw = "SuperSecret123!"
    hashed = hash_password(pw)
    assert hashed != pw
    assert verify_password(pw, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_generation_and_decoding():
    token = create_access_token(
        subject="user-uuid-123",
        role="creator",
        organization_id="org-uuid-456",
        email="alex@acme.demo",
        expires_delta=timedelta(minutes=15)
    )
    assert token is not None

    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "user-uuid-123"
    assert payload["role"] == "creator"
    assert payload["email"] == "alex@acme.demo"
    assert payload["org_id"] == "org-uuid-456"


def test_user_registration_and_duplicate_check(db):
    user_in = UserRegister(
        email="newuser@acme.demo",
        password="Password@123",
        full_name="New Test User",
        role="creator",
        organization_name="Acme Labs"
    )

    result = register(user_in=user_in, db=db)
    assert result.access_token is not None
    assert result.user.email == "newuser@acme.demo"
    assert result.user.role == "creator"
    assert result.user.organization_name == "Acme Labs"

    # Duplicate registration must fail with 400
    with pytest.raises(HTTPException) as exc_info:
        register(user_in=user_in, db=db)
    assert exc_info.value.status_code == 400


def test_user_login_valid_and_invalid(db):
    user_in = UserRegister(
        email="logintest@acme.demo",
        password="SecurePass@123",
        full_name="Login Tester",
        role="reviewer"
    )
    register(user_in=user_in, db=db)

    # Valid login
    login_valid = UserLogin(email="logintest@acme.demo", password="SecurePass@123")
    res = login(login_data=login_valid, db=db)
    assert res.access_token is not None
    assert res.user.role == "reviewer"

    # Invalid password
    login_invalid = UserLogin(email="logintest@acme.demo", password="WrongPassword")
    with pytest.raises(HTTPException) as exc_info:
        login(login_data=login_invalid, db=db)
    assert exc_info.value.status_code == 401


def test_demo_login_for_all_personas(db):
    """Verify instant 1-click login for Creator, Reviewer, and Admin personas."""
    for role in ["creator", "reviewer", "admin"]:
        req = DemoLoginRequest(role=role)
        res = demo_login(req=req, db=db)
        assert res.access_token is not None
        assert res.user.role == role
        assert f"{role}@contentguard.demo" in res.user.email


def test_rbac_role_checker_enforcement():
    """Verify that RoleChecker enforces required permissions and rejects unauthorized roles."""
    admin_checker = RoleChecker(["admin"])
    reviewer_checker = RoleChecker(["reviewer", "admin"])

    admin_user = User(id="1", role="admin", is_active=True, email="admin@test.com", full_name="A", hashed_password="x", organization_id="1")
    reviewer_user = User(id="2", role="reviewer", is_active=True, email="rev@test.com", full_name="R", hashed_password="x", organization_id="1")
    creator_user = User(id="3", role="creator", is_active=True, email="creat@test.com", full_name="C", hashed_password="x", organization_id="1")

    # Admin passes both
    assert admin_checker(admin_user).role == "admin"
    assert reviewer_checker(admin_user).role == "admin"

    # Reviewer passes reviewer check, fails admin check
    assert reviewer_checker(reviewer_user).role == "reviewer"
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(reviewer_user)
    assert exc_info.value.status_code == 403

    # Creator fails both
    with pytest.raises(HTTPException) as exc_info:
        admin_checker(creator_user)
    assert exc_info.value.status_code == 403

    with pytest.raises(HTTPException) as exc_info:
        reviewer_checker(creator_user)
    assert exc_info.value.status_code == 403
