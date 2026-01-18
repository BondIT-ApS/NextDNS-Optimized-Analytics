# file: backend/tests/unit/test_auth.py
"""
Unit tests for authentication module (auth.py).

Tests password hashing, JWT token creation/validation, and user authentication.
"""

from datetime import datetime, timedelta, timezone

import pytest
from freezegun import freeze_time

from auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    authenticate_user,
)


@pytest.mark.unit
@pytest.mark.skip(reason="bcrypt/passlib compatibility issue with Python 3.14")
def test_password_hashing():
    """Test password hashing produces a valid bcrypt hash."""
    password = "secure123"
    hashed = get_password_hash(password)

    assert hashed is not None
    assert hashed.startswith("$2b$")  # bcrypt hash prefix
    assert len(hashed) > 50  # bcrypt hashes are long
    assert hashed != password  # Hash should be different from plain password


@pytest.mark.unit
@pytest.mark.skip(reason="bcrypt/passlib compatibility issue with Python 3.14")
def test_verify_password_correct():
    """Test password verification succeeds with correct password."""
    password = "correct_pass"
    hashed = get_password_hash(password)

    assert verify_password(password, hashed) is True


@pytest.mark.unit
@pytest.mark.skip(reason="bcrypt/passlib compatibility issue with Python 3.14")
def test_verify_password_incorrect():
    """Test password verification fails with incorrect password."""
    password = "correct_pass"
    wrong_password = "wrong_pass"
    hashed = get_password_hash(password)

    assert verify_password(wrong_password, hashed) is False


@pytest.mark.unit
def test_create_access_token_basic():
    """Test JWT token creation with basic data."""
    data = {"sub": "testuser"}
    token = create_access_token(data)

    assert token is not None
    assert isinstance(token, str)
    assert len(token) > 0
    # JWT tokens have format: header.payload.signature
    assert token.count(".") == 2


@pytest.mark.unit
def test_create_access_token_with_expiration():
    """Test JWT token creation with custom expiration."""
    data = {"sub": "testuser"}
    expires_delta = timedelta(hours=2)
    token = create_access_token(data, expires_delta=expires_delta)

    assert token is not None
    # Decode and verify expiration was set
    payload = decode_access_token(token)
    assert payload is not None
    assert "exp" in payload


@pytest.mark.unit
@freeze_time("2024-01-15 12:00:00")
def test_decode_access_token_valid():
    """Test decoding a valid JWT token."""
    data = {"sub": "testuser", "role": "admin"}
    token = create_access_token(data)

    payload = decode_access_token(token)

    assert payload is not None
    assert payload["sub"] == "testuser"
    assert payload["role"] == "admin"
    assert "exp" in payload


@pytest.mark.unit
def test_decode_access_token_invalid():
    """Test decoding an invalid JWT token returns None."""
    invalid_token = "not.a.valid.token"

    payload = decode_access_token(invalid_token)

    assert payload is None


@pytest.mark.unit
def test_decode_access_token_malformed():
    """Test decoding a malformed JWT token returns None."""
    malformed_token = "malformed_token_without_dots"

    payload = decode_access_token(malformed_token)

    assert payload is None


@pytest.mark.unit
def test_authenticate_user_valid_plain_password(monkeypatch):
    """Test user authentication with plain text password."""
    monkeypatch.setenv("AUTH_USERNAME", "testuser")
    monkeypatch.setenv("AUTH_PASSWORD", "plainpassword")

    # Need to reload auth module to pick up env changes
    import importlib
    import auth

    importlib.reload(auth)

    result = auth.authenticate_user("testuser", "plainpassword")

    assert result is True


@pytest.mark.unit
def test_authenticate_user_invalid_username(monkeypatch):
    """Test user authentication fails with invalid username."""
    monkeypatch.setenv("AUTH_USERNAME", "correctuser")
    monkeypatch.setenv("AUTH_PASSWORD", "password")

    import importlib
    import auth

    importlib.reload(auth)

    result = auth.authenticate_user("wronguser", "password")

    assert result is False


@pytest.mark.unit
def test_authenticate_user_invalid_password(monkeypatch):
    """Test user authentication fails with invalid password."""
    monkeypatch.setenv("AUTH_USERNAME", "testuser")
    monkeypatch.setenv("AUTH_PASSWORD", "correctpassword")

    import importlib
    import auth

    importlib.reload(auth)

    result = auth.authenticate_user("testuser", "wrongpassword")

    assert result is False


@pytest.mark.unit
@pytest.mark.skip(reason="bcrypt/passlib compatibility issue with Python 3.14")
def test_authenticate_user_with_hashed_password(monkeypatch):
    """Test user authentication with bcrypt hashed password."""
    plain_password = "secure123"
    hashed_password = get_password_hash(plain_password)

    monkeypatch.setenv("AUTH_USERNAME", "testuser")
    monkeypatch.setenv("AUTH_PASSWORD", hashed_password)

    import importlib
    import auth

    importlib.reload(auth)

    result = auth.authenticate_user("testuser", plain_password)

    assert result is True


@pytest.mark.unit
@freeze_time("2024-01-15 12:00:00")
def test_token_expiration_set_correctly(monkeypatch):
    """Test that token expiration is set correctly based on session timeout."""
    monkeypatch.setenv("AUTH_SESSION_TIMEOUT", "30")

    import importlib
    import auth

    importlib.reload(auth)

    data = {"sub": "testuser"}
    token = auth.create_access_token(data)
    payload = auth.decode_access_token(token)

    assert payload is not None
    exp_timestamp = payload["exp"]
    exp_datetime = datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)

    # Should expire in 30 minutes from frozen time
    expected_expiry = datetime(2024, 1, 15, 12, 30, 0, tzinfo=timezone.utc)
    assert exp_datetime == expected_expiry
