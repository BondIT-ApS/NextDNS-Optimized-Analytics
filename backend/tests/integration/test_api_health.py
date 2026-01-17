# file: backend/tests/integration/test_api_health.py
"""
🧱 Integration Tests for Health API Endpoints

Testing the heartbeat of our LEGO construction!
"""

import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_simple(self, test_client):
        """Test basic health endpoint."""
        response = test_client.get("/health")

        # Health endpoint may return 503 if database is not available in test
        # This is expected behavior for the infrastructure tests
        assert response.status_code in [200, 503]
        data = response.json()

        # When status is 503, response is wrapped in 'detail' field
        if response.status_code == 503:
            assert "detail" in data
            assert "status" in data["detail"]
            assert data["detail"]["status"] == "unhealthy"
        else:
            assert "status" in data
            assert data["status"] == "healthy"

    def test_health_endpoint_detailed(self, test_client):
        """Test detailed health endpoint."""
        response = test_client.get("/health/detailed")

        # Health endpoint may return 503 if database is not available in test
        # This is expected behavior for the infrastructure tests
        assert response.status_code in [200, 503]
        data = response.json()

        # When status is 503, response is wrapped in 'detail' field
        if response.status_code == 503:
            assert "detail" in data
            assert "status_api" in data["detail"]
            assert "status_db" in data["detail"]
            assert data["detail"]["status_api"] == "unhealthy"
            assert data["detail"]["healthy"] is False
        else:
            # Healthy response has these top-level fields
            assert "status_api" in data
            assert "status_db" in data
            assert data["status_api"] == "healthy"
            assert data["healthy"] is True
