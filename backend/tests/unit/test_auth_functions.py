# file: backend/tests/unit/test_auth_functions.py
"""
Additional unit tests for auth.py functions to improve coverage.

Tests authentication dependency functions and initialization.
"""

import sys
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_when_auth_disabled(monkeypatch):
    """Test get_current_user returns 'anonymous' when AUTH_ENABLED=false."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    # Mock auth disabled
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user

        # Should return anonymous without credentials
        result = await get_current_user(credentials=None)
        assert result == "anonymous"
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_no_credentials_when_auth_enabled(monkeypatch):
    """Test get_current_user raises 401 when no credentials provided and auth enabled."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user

        # Should raise 401 when credentials missing
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=None)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Not authenticated"
        assert "WWW-Authenticate" in exc_info.value.headers
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch):
    """Test get_current_user raises 401 with invalid token."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user

        # Create invalid credentials
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.here"
        )

        # Should raise 401 for invalid token
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=invalid_credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authentication credentials"
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_token_without_username(monkeypatch):
    """Test get_current_user raises 401 when token payload missing 'sub' field."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user, create_access_token

        # Create token without 'sub' field
        token = create_access_token({"role": "admin"})  # Missing 'sub'
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        # Should raise 401 when username (sub) is missing
        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(credentials=credentials)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail == "Invalid authentication credentials"
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_when_auth_disabled(monkeypatch):
    """Test get_current_user_optional returns None when AUTH_ENABLED=false."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user_optional

        # Should return None when auth disabled
        result = await get_current_user_optional(credentials=None)
        assert result is None
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_no_credentials(monkeypatch):
    """Test get_current_user_optional returns None when no credentials provided."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user_optional

        # Should return None (not raise exception) when credentials missing
        result = await get_current_user_optional(credentials=None)
        assert result is None
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_invalid_token(monkeypatch):
    """Test get_current_user_optional returns None with invalid token."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user_optional

        # Create invalid credentials
        invalid_credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials="invalid.token.here"
        )

        # Should return None (not raise exception) for invalid token
        result = await get_current_user_optional(credentials=invalid_credentials)
        assert result is None
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_token_without_username(monkeypatch):
    """Test get_current_user_optional returns None when token missing 'sub'."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user_optional, create_access_token

        # Create token without 'sub' field
        token = create_access_token({"role": "admin"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        # Should return None when username is missing
        result = await get_current_user_optional(credentials=credentials)
        assert result is None
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_valid_token(monkeypatch):
    """Test get_current_user_optional returns username with valid token."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import get_current_user_optional, create_access_token

        # Create valid token
        token = create_access_token({"sub": "testuser"})
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer", credentials=token
        )

        # Should return username
        result = await get_current_user_optional(credentials=credentials)
        assert result == "testuser"
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
def test_init_auth_when_enabled(monkeypatch, caplog):
    """Test init_auth logs correct messages when authentication is enabled."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secure_password")
    monkeypatch.setenv("AUTH_SECRET_KEY", "custom-secret-key-not-default-12345678")
    monkeypatch.setenv("AUTH_SESSION_TIMEOUT", "60")

    try:
        from auth import init_auth

        # Call init_auth
        with caplog.at_level("INFO"):
            init_auth()

        # Verify log messages
        assert "Authentication system ENABLED" in caplog.text
        assert "Session timeout: 60 minutes" in caplog.text
        assert "Configured username: admin" in caplog.text
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
def test_init_auth_when_disabled(monkeypatch, caplog):
    """Test init_auth logs correct message when authentication is disabled."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    try:
        from auth import init_auth

        # Call init_auth
        with caplog.at_level("INFO"):
            init_auth()

        # Verify log message
        assert (
            "Authentication system DISABLED - all routes are public" in caplog.text
        )
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]


@pytest.mark.unit
def test_init_auth_warning_no_password(monkeypatch, caplog):
    """Test init_auth logs warning when AUTH_PASSWORD is not set."""
    # Remove auth module if already imported
    if "auth" in sys.modules:
        del sys.modules["auth"]

    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_PASSWORD", "")  # Empty password
    monkeypatch.setenv("AUTH_SECRET_KEY", "custom-secret-key-not-default-12345678")

    try:
        from auth import init_auth

        # Call init_auth
        with caplog.at_level("WARNING"):
            init_auth()

        # Verify warning message
        assert "AUTH_PASSWORD not set" in caplog.text
        assert "Authentication will not work properly" in caplog.text
    finally:
        # Clean up
        if "auth" in sys.modules:
            del sys.modules["auth"]
