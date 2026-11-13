import bcrypt
import jwt
import pyotp
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, Tuple
from app.core.config import settings


def hash_password(password: str) -> str:
    """Hash a plaintext password using bcrypt with a generated salt."""
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False


def validate_password_complexity(password: str) -> Tuple[bool, str]:
    """
    Validate that password meets zero-trust security standards:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special symbol
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)."
    return True, "Password meets complexity requirements."


def create_access_token(
    subject: str,
    role: str,
    organization_id: str,
    email: str,
    expires_delta: Optional[timedelta] = None
) -> str:
    """Generate a signed JWT token containing user identity and role claims."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "email": email,
        "role": role,
        "org_id": organization_id,
        "type": "access",
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def create_refresh_token(
    subject: str,
    organization_id: str,
    expires_delta: Optional[timedelta] = None
) -> Tuple[str, datetime]:
    """Generate a signed refresh JWT token valid for 7 days by default."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=7)

    to_encode: Dict[str, Any] = {
        "sub": subject,
        "org_id": organization_id,
        "type": "refresh",
        "jti": str(uuid.uuid4()),
        "exp": expire,
        "iat": datetime.now(timezone.utc)
    }

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt, expire


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate an access JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except (jwt.PyJWTError, Exception):
        return None


def decode_refresh_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a refresh JWT token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload
    except (jwt.PyJWTError, Exception):
        return None


# --- TOTP MFA Support ---
def generate_totp_secret() -> str:
    """Generate a cryptographically secure random base32 secret for TOTP MFA."""
    return pyotp.random_base32()


def get_totp_uri(secret: str, email: str, issuer_name: str = "ContentGuard AI") -> str:
    """Generate the otpauth:// URI for QR code generation in authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer_name)


def verify_totp(secret: str, code: str) -> bool:
    """Verify a 6-digit TOTP code with standard 30-second time-step tolerance."""
    if not secret or not code:
        return False
    try:
        totp = pyotp.TOTP(secret)
        return totp.verify(code.strip(), valid_window=1)
    except Exception:
        return False


DISPOSABLE_DOMAINS = {
    "tempmail.com", "throwawaymail.com", "mailinator.com", "guerrillamail.com",
    "sharklasers.com", "10minutemail.com", "trashmail.com", "yopmail.com",
    "dispostable.com", "fakeinbox.com"
}


def validate_email_address(email: str) -> Tuple[bool, str]:
    """
    Validates email syntax, domain structure, and checks against disposable domains.
    """
    if not email or len(email.strip()) < 5:
        return False, "Email address is required."

    cleaned = email.strip().lower()
    email_regex = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
    if not re.match(email_regex, cleaned):
        return False, "Please provide a valid email format (e.g., user@company.com)."

    domain = cleaned.split("@")[-1]
    if "." not in domain or len(domain.split(".")[-1]) < 2:
        return False, "Email domain appears invalid or incomplete."

    if domain in DISPOSABLE_DOMAINS:
        return False, "Temporary and disposable email domains are not permitted for enterprise registration."

    return True, "Email is valid."

