import pytest
from app.core.security import validate_email_address, validate_password_complexity
from app.api.v1.endpoints.auth import register, verify_email, resend_verification, forgot_password, reset_password
from app.schemas.auth import (
    UserRegister,
    VerifyEmailRequest,
    ResendVerificationRequest,
    ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.models.user import User


def test_email_validation_rules():
    # Valid enterprise emails
    assert validate_email_address("alex@acme.com")[0] is True
    assert validate_email_address("sarah.connor@cyberdyne.org")[0] is True

    # Invalid formats
    assert validate_email_address("notanemail")[0] is False
    assert validate_email_address("missingatsign.com")[0] is False
    assert validate_email_address("@nodomain.com")[0] is False
    assert validate_email_address("user@domain")[0] is False

    # Disposable emails
    assert validate_email_address("test@tempmail.com")[0] is False
    assert validate_email_address("spam@mailinator.com")[0] is False


def test_email_verification_and_reset_flow(db):
    email = "unique.employee@enterprisecorp.io"
    user_in = UserRegister(
        email=email,
        password="ValidPassword@2026",
        full_name="Enterprise Employee",
        organization_name="Enterprise Corp"
    )
    reg_resp = register(user_in, db=db)
    assert reg_resp.access_token is not None
    assert reg_resp.user.email == email

    user = db.query(User).filter(User.email == email).first()
    assert user is not None
    user.is_verified = False
    db.commit()

    # Test resend verification
    resend_resp = resend_verification(ResendVerificationRequest(email=email), db=db)
    assert "Verification code dispatched" in resend_resp["message"]
    token = resend_resp["verification_token"]

    # Test verify email
    verify_resp = verify_email(VerifyEmailRequest(token=token), db=db)
    assert "verified successfully" in verify_resp["message"]
    assert user.is_verified is True

    # Test forgot password
    forgot_resp = forgot_password(ForgotPasswordRequest(email=email), db=db)
    assert "Password reset token generated" in forgot_resp["message"]
    reset_token = forgot_resp["reset_token"]

    # Test reset password
    reset_resp = reset_password(ResetPasswordRequest(token=reset_token, new_password="NewSecurePassword@2026"), db=db)
    assert "successfully reset" in reset_resp["message"]
