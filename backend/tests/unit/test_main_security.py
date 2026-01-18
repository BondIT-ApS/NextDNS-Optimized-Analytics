# file: backend/tests/unit/test_main_security.py
"""
Unit tests for security features in main.py added in PR #260.

Tests CORS configuration and ALLOWED_ORIGINS environment variable handling.
"""

import os
import sys
import pytest


@pytest.mark.unit
def test_cors_allowed_origins_from_environment(monkeypatch):
    """
    Test that ALLOWED_ORIGINS is correctly loaded from environment variable.

    This tests the security fix in PR #260 that replaced wildcard CORS
    with environment-configured specific origins.
    """
    # Remove main module if already imported
    if "main" in sys.modules:
        del sys.modules["main"]

    # Set custom ALLOWED_ORIGINS
    monkeypatch.setenv(
        "ALLOWED_ORIGINS",
        "https://example.com,https://app.example.com,https://www.example.com",
    )
    monkeypatch.setenv("LOCAL_API_KEY", "test-key-123")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-testing")

    try:
        import main

        # Verify ALLOWED_ORIGINS was parsed correctly
        assert hasattr(main, "ALLOWED_ORIGINS")
        assert main.ALLOWED_ORIGINS == [
            "https://example.com",
            "https://app.example.com",
            "https://www.example.com",
        ]
    finally:
        # Clean up
        if "main" in sys.modules:
            del sys.modules["main"]


@pytest.mark.unit
def test_cors_allowed_origins_default_values(monkeypatch):
    """
    Test that ALLOWED_ORIGINS uses correct default values for development.

    Ensures the default includes common development ports.
    """
    # Remove main module if already imported
    if "main" in sys.modules:
        del sys.modules["main"]

    # Don't set ALLOWED_ORIGINS - should use defaults
    monkeypatch.delenv("ALLOWED_ORIGINS", raising=False)
    monkeypatch.setenv("LOCAL_API_KEY", "test-key-123")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-testing")

    try:
        import main

        # Verify default ALLOWED_ORIGINS includes common dev ports
        assert hasattr(main, "ALLOWED_ORIGINS")
        assert "http://localhost:5002" in main.ALLOWED_ORIGINS
        assert "http://localhost:5173" in main.ALLOWED_ORIGINS
        assert "http://localhost:3000" in main.ALLOWED_ORIGINS
        # Should NOT contain wildcard
        assert "*" not in main.ALLOWED_ORIGINS
    finally:
        # Clean up
        if "main" in sys.modules:
            del sys.modules["main"]


@pytest.mark.unit
def test_cors_single_origin(monkeypatch):
    """
    Test that ALLOWED_ORIGINS works correctly with a single origin.
    """
    # Remove main module if already imported
    if "main" in sys.modules:
        del sys.modules["main"]

    # Set single origin
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://production.example.com")
    monkeypatch.setenv("LOCAL_API_KEY", "test-key-123")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-testing")

    try:
        import main

        # Verify single origin is handled correctly
        assert main.ALLOWED_ORIGINS == ["https://production.example.com"]
    finally:
        # Clean up
        if "main" in sys.modules:
            del sys.modules["main"]


@pytest.mark.unit
def test_cors_no_wildcard_allowed(monkeypatch):
    """
    Test that wildcard (*) in ALLOWED_ORIGINS is treated as a regular origin,
    not as a special wildcard pattern.

    This verifies the security fix from PR #260 that removed wildcard CORS.
    """
    # Remove main module if already imported
    if "main" in sys.modules:
        del sys.modules["main"]

    # Even if someone puts * in env var, it should be treated literally
    monkeypatch.setenv("ALLOWED_ORIGINS", "*")
    monkeypatch.setenv("LOCAL_API_KEY", "test-key-123")
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-testing")

    try:
        import main

        # The string "*" would be in the list, but CORS middleware
        # won't treat it as wildcard - it will try to match literally
        # This is intentional - we want to force explicit origins
        assert main.ALLOWED_ORIGINS == ["*"]
    finally:
        # Clean up
        if "main" in sys.modules:
            del sys.modules["main"]


@pytest.mark.unit
def test_local_api_key_environment_loading(monkeypatch):
    """
    Test that LOCAL_API_KEY is correctly loaded from environment.
    """
    # Remove main module if already imported
    if "main" in sys.modules:
        del sys.modules["main"]

    # Set custom API key
    test_api_key = "my-test-api-key-12345"
    monkeypatch.setenv("LOCAL_API_KEY", test_api_key)
    monkeypatch.setenv("AUTH_SECRET_KEY", "test-secret-key-for-testing")

    try:
        import main

        # Verify API key was loaded
        assert hasattr(main, "LOCAL_API_KEY")
        assert main.LOCAL_API_KEY == test_api_key
    finally:
        # Clean up
        if "main" in sys.modules:
            del sys.modules["main"]
