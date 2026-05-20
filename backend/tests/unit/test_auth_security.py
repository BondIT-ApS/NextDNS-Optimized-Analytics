# file: backend/tests/unit/test_auth_security.py
"""
Unit tests for authentication security features added in PR #260.

Tests the security validation that prevents using default test keys in production.
"""

import pytest


@pytest.mark.unit
def test_auth_secret_key_validation_with_default_key(monkeypatch, reload_auth_module):
    """
    Test that importing auth module with AUTH_ENABLED=true and default
    AUTH_SECRET_KEY raises a ValueError with clear error message.

    This tests the security validation added in PR #260 that prevents
    accidentally using the test secret key in production.
    """
    monkeypatch.setenv("AUTH_ENABLED", "true")
    # Don't set AUTH_SECRET_KEY - it will use the default test key
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)

    with pytest.raises(ValueError) as exc_info:
        import auth  # noqa: F401  # pylint: disable=unused-import

    error_message = str(exc_info.value)
    assert "AUTH_SECRET_KEY must be set to a secure value" in error_message
    assert "authentication is enabled" in error_message


@pytest.mark.unit
def test_auth_secret_key_validation_with_custom_key(monkeypatch, reload_auth_module):
    """
    Test that providing a custom AUTH_SECRET_KEY when AUTH_ENABLED=true
    works correctly without raising an error.
    """
    monkeypatch.setenv("AUTH_ENABLED", "true")
    monkeypatch.setenv(
        "AUTH_SECRET_KEY", "my-secure-custom-key-for-production-use-12345678"
    )

    import auth

    assert auth.AUTH_ENABLED is True
    assert auth.AUTH_SECRET_KEY == "my-secure-custom-key-for-production-use-12345678"
    assert (
        auth.AUTH_SECRET_KEY
        != "test-secret-key-for-testing-only-do-not-use-in-production-min-32-chars"
    )


@pytest.mark.unit
def test_auth_secret_key_default_when_auth_disabled(monkeypatch, reload_auth_module):
    """
    Test that the default test secret key is allowed when AUTH_ENABLED=false.

    This ensures tests can run without explicitly setting AUTH_SECRET_KEY.
    """
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.delenv("AUTH_SECRET_KEY", raising=False)

    import auth

    assert auth.AUTH_ENABLED is False
    assert (
        auth.AUTH_SECRET_KEY
        == "test-secret-key-for-testing-only-do-not-use-in-production-min-32-chars"
    )


@pytest.mark.unit
def test_auth_config_values_from_environment(monkeypatch, reload_auth_module):
    """
    Test that authentication configuration values are correctly loaded
    from environment variables.
    """
    monkeypatch.setenv("AUTH_ENABLED", "false")
    monkeypatch.setenv("AUTH_USERNAME", "custom_admin")
    monkeypatch.setenv("AUTH_PASSWORD", "custom_password")
    monkeypatch.setenv("AUTH_SECRET_KEY", "custom-secret-key-1234567890")
    monkeypatch.setenv("AUTH_SESSION_TIMEOUT", "120")

    import auth

    assert auth.AUTH_ENABLED is False
    assert auth.AUTH_USERNAME == "custom_admin"
    assert auth.AUTH_PASSWORD == "custom_password"
    assert auth.AUTH_SECRET_KEY == "custom-secret-key-1234567890"
    assert auth.AUTH_SESSION_TIMEOUT == 120
    assert auth.AUTH_ALGORITHM == "HS256"  # Should be constant
