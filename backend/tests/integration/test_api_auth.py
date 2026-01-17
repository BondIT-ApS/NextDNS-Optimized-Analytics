# file: backend/tests/integration/test_api_auth.py
"""
Integration tests for authentication API endpoints.

Tests the /auth/* endpoints including login, logout, status, and config.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.integration
def test_auth_config_endpoint(test_client):
    """Test GET /auth/config returns correct config."""
    response = test_client.get("/auth/config")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "enabled" in data
    assert "session_timeout_minutes" in data
    assert isinstance(data["enabled"], bool)
    assert isinstance(data["session_timeout_minutes"], int)


@pytest.mark.integration
def test_logout_endpoint(test_client):
    """Test POST /auth/logout returns success message."""
    response = test_client.post("/auth/logout")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
    assert "logged out" in data["message"].lower()


@pytest.mark.integration
def test_auth_status_without_token(test_client):
    """Test GET /auth/status without token (works when auth is disabled)."""
    response = test_client.get("/auth/status")

    # When auth is disabled, it returns 200 with authenticated=False
    # When auth is enabled, it returns 401
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED]

    if response.status_code == status.HTTP_200_OK:
        data = response.json()
        assert "authenticated" in data
        assert "username" in data


@pytest.mark.integration
def test_login_endpoint_structure(test_client):
    """Test POST /auth/login endpoint structure and response format."""
    # Test that the endpoint exists and returns proper error format
    response = test_client.post(
        "/auth/login",
        json={"username": "testuser", "password": "testpass"}
    )

    # Should return either 400 (auth disabled) or 401 (invalid credentials)
    assert response.status_code in [
        status.HTTP_400_BAD_REQUEST,
        status.HTTP_401_UNAUTHORIZED
    ]
    assert "detail" in response.json()
