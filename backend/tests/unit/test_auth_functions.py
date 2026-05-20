# file: backend/tests/unit/test_auth_functions.py
"""
Additional unit tests for auth.py functions to improve coverage.

Tests authentication dependency functions and initialization.
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_when_auth_disabled(monkeypatch, reload_auth_module):
    """Test get_current_user returns 'anonymous' when AUTH_ENABLED=false."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user

    result = await get_current_user(credentials=None)
    assert result == "anonymous"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_no_credentials_when_auth_enabled(
    monkeypatch, reload_auth_module
):
    """Test get_current_user raises 401 when no credentials provided and auth enabled."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=None)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Not authenticated"
    assert "WWW-Authenticate" in exc_info.value.headers


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_invalid_token(monkeypatch, reload_auth_module):
    """Test get_current_user raises 401 with invalid token."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user

    invalid_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid.token.here"
    )

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=invalid_credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_token_without_username(monkeypatch, reload_auth_module):
    """Test get_current_user raises 401 when token payload missing 'sub' field."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user, create_access_token

    token = create_access_token({"role": "admin"})  # Missing 'sub'
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials=credentials)

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Invalid authentication credentials"


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_when_auth_disabled(
    monkeypatch, reload_auth_module
):
    """Test get_current_user_optional returns None when AUTH_ENABLED=false."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user_optional

    result = await get_current_user_optional(credentials=None)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_no_credentials(
    monkeypatch, reload_auth_module
):
    """Test get_current_user_optional returns None when no credentials provided."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user_optional

    result = await get_current_user_optional(credentials=None)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_invalid_token(monkeypatch, reload_auth_module):
    """Test get_current_user_optional returns None with invalid token."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user_optional

    invalid_credentials = HTTPAuthorizationCredentials(
        scheme="Bearer", credentials="invalid.token.here"
    )

    result = await get_current_user_optional(credentials=invalid_credentials)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_token_without_username(
    monkeypatch, reload_auth_module
):
    """Test get_current_user_optional returns None when token missing 'sub'."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user_optional, create_access_token

    token = create_access_token({"role": "admin"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    result = await get_current_user_optional(credentials=credentials)
    assert result is None


@pytest.mark.unit
@pytest.mark.asyncio
async def test_get_current_user_optional_valid_token(monkeypatch, reload_auth_module):
    """Test get_current_user_optional returns username with valid token."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import get_current_user_optional, create_access_token

    token = create_access_token({"sub": "testuser"})
    credentials = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    result = await get_current_user_optional(credentials=credentials)
    assert result == "testuser"


@pytest.mark.unit
def test_init_auth_when_enabled(monkeypatch, caplog, reload_auth_module):
    """Test init_auth logs correct messages when authentication is enabled."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_USERNAME", "admin")
    monkeypatch.setenv("AUTH_PASSWORD", "secure_password")
    monkeypatch.setenv("AUTH_SECRET_KEY", "custom-secret-key-not-default-12345678")
    monkeypatch.setenv("AUTH_SESSION_TIMEOUT", "60")

    from auth import init_auth

    with caplog.at_level("INFO"):
        init_auth()

    assert "Authentication system ENABLED" in caplog.text
    assert "Session timeout: 60 minutes" in caplog.text
    assert "Configured username: admin" in caplog.text


@pytest.mark.unit
def test_init_auth_when_disabled(monkeypatch, caplog, reload_auth_module):
    """Test init_auth logs correct message when authentication is disabled."""
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "test-secret-key-for-testing-only-min-32-chars"
    )

    from auth import init_auth

    with caplog.at_level("INFO"):
        init_auth()

    assert "Authentication system DISABLED - all routes are public" in caplog.text


@pytest.mark.unit
def test_init_auth_warning_no_password(monkeypatch, caplog, reload_auth_module):
    """Test init_auth logs warning when AUTH_PASSWORD is not set."""
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv("AUTH_PASSWORD", "")  # Empty password
    monkeypatch.setenv("AUTH_SECRET_KEY", "custom-secret-key-not-default-12345678")

    from auth import init_auth

    with caplog.at_level("WARNING"):
        init_auth()

    assert "AUTH_PASSWORD not set" in caplog.text
    assert "Authentication will not work properly" in caplog.text
