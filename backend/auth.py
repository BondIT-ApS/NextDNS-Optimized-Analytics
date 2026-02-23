# file: backend/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from jwt.exceptions import InvalidTokenError as JWTError
from passlib.context import CryptContext
from pydantic import BaseModel

from logging_config import get_logger

logger = get_logger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security bearer for JWT tokens
security = HTTPBearer(auto_error=False)

# Environment variables for authentication
AUTH_ENABLED = os.getenv("AUTH_ENABLED", "false").lower() == "true"
AUTH_USERNAME = os.getenv("AUTH_USERNAME", "admin")
AUTH_PASSWORD = os.getenv("AUTH_PASSWORD", "")
# Provide a default for testing, but it will be rejected if AUTH_ENABLED=true
AUTH_SECRET_KEY = os.getenv(
    "AUTH_SECRET_KEY",
    "test-secret-key-for-testing-only-do-not-use-in-production-min-32-chars",
)
AUTH_ALGORITHM = "HS256"
AUTH_SESSION_TIMEOUT = int(os.getenv("AUTH_SESSION_TIMEOUT", "60"))  # minutes

# Validate AUTH_SECRET_KEY when authentication is enabled (production)
if (
    AUTH_ENABLED
    and AUTH_SECRET_KEY
    == "test-secret-key-for-testing-only-do-not-use-in-production-min-32-chars"
):
    logger.critical(
        "❌ SECURITY ERROR: AUTH_SECRET_KEY must be set to a secure value when AUTH_ENABLED=true"
    )
    logger.critical("💡 Generate a secure key with: openssl rand -hex 32")
    logger.critical("💡 Add to .env file: AUTH_SECRET_KEY=<generated-key>")
    logger.critical("❌ The default test key cannot be used in production!")
    raise ValueError(
        "AUTH_SECRET_KEY must be set to a secure value when authentication is enabled. "
        "Set AUTH_SECRET_KEY environment variable."
    )


# Pydantic models
class LoginRequest(BaseModel):
    """Login request model."""

    username: str
    password: str


class LoginResponse(BaseModel):
    """Login response model."""

    access_token: str
    token_type: str
    expires_in: int


class AuthStatus(BaseModel):
    """Authentication status model."""

    authenticated: bool
    username: Optional[str] = None


class AuthConfig(BaseModel):
    """Authentication configuration model."""

    enabled: bool
    session_timeout_minutes: int


# Password hashing functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Generate a password hash."""
    return pwd_context.hash(password)


# JWT token functions
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=AUTH_SESSION_TIMEOUT)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, AUTH_SECRET_KEY, algorithm=AUTH_ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT access token."""
    try:
        payload = jwt.decode(token, AUTH_SECRET_KEY, algorithms=[AUTH_ALGORITHM])
        return payload
    except JWTError as e:
        logger.debug(f"🔒 JWT decode error: {e}")
        return None


# Authentication functions
def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password."""
    if username != AUTH_USERNAME:
        logger.warning(f"🔒 Authentication failed: invalid username '{username}'")
        return False

    # If AUTH_PASSWORD is already a hash (starts with $2b$), verify against it
    # Otherwise, hash the plain password and compare
    if AUTH_PASSWORD.startswith("$2b$") or AUTH_PASSWORD.startswith("$2a$"):
        # It's already a hash, verify directly
        is_valid = verify_password(password, AUTH_PASSWORD)
    else:
        # It's a plain password, hash and compare
        # This allows users to just put plain passwords in .env
        is_valid = password == AUTH_PASSWORD

    if not is_valid:
        logger.warning(
            f"🔒 Authentication failed: invalid password for user '{username}'"
        )
    else:
        logger.info(f"🔒 User '{username}' authenticated successfully")

    return is_valid


# Dependency for optional authentication
async def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Optional[str]:
    """Get current user if authenticated, None otherwise. Used when auth is disabled."""
    if not AUTH_ENABLED:
        return None

    if not credentials:
        return None

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        return None

    username: str = payload.get("sub")
    if username is None:
        return None

    return username


# Dependency for required authentication
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """Get current user. Raises 401 if not authenticated and auth is enabled."""
    if not AUTH_ENABLED:
        # If auth is disabled, return a dummy user
        return "anonymous"

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    username: str = payload.get("sub")
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return username


# Initialize authentication system
def init_auth():
    """Initialize authentication system and log configuration."""
    if AUTH_ENABLED:
        logger.info("🔒 Authentication system ENABLED")
        logger.info(f"🔒 Session timeout: {AUTH_SESSION_TIMEOUT} minutes")
        logger.info(f"🔒 Configured username: {AUTH_USERNAME}")
        if not AUTH_PASSWORD:
            logger.warning(
                "⚠️  AUTH_PASSWORD not set! Authentication will not work properly."
            )
        if AUTH_SECRET_KEY == "default-secret-key-change-in-production":
            logger.warning(
                "⚠️  Using default AUTH_SECRET_KEY! Generate a secure key for production."
            )
    else:
        logger.info("🔓 Authentication system DISABLED - all routes are public")
