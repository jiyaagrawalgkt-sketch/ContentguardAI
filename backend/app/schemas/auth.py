from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime


class UserRegister(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password with minimum 6 characters")
    full_name: str = Field(..., min_length=2)
    role: Optional[str] = Field("creator", description="Role: creator, reviewer, or admin")
    organization_name: Optional[str] = Field(None, description="Optional organization name")


class UserLogin(BaseModel):
    email: str
    password: str


class GoogleLoginRequest(BaseModel):
    credential: str = Field(..., description="Google ID Token (JWT) from Google Identity Services")


class DemoLoginRequest(BaseModel):
    role: str = Field(..., description="Role to switch into: creator, reviewer, or admin")


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    full_name: str
    role: str
    organization_id: str
    organization_name: Optional[str] = None
    is_active: bool
    is_verified: bool = True
    created_at: datetime


class Token(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"
    user: UserOut


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class MFASetupResponse(BaseModel):
    secret: str
    otpauth_url: str


class MFAVerifyRequest(BaseModel):
    code: str


class TokenPayload(BaseModel):
    sub: str
    email: str
    role: str
    org_id: str
    exp: int


class VerifyEmailRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ResendVerificationRequest(BaseModel):
    email: str = Field(..., description="User email address")


class ForgotPasswordRequest(BaseModel):
    email: str = Field(..., description="User email address")


class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6)
