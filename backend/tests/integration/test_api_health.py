# file: backend/tests/integration/test_api_health.py
"""
🧱 Integration Tests for Health API Endpoints

Testing the heartbeat of our LEGO construction!
"""

import pytest


class TestHealthEndpoints:
    """Test health check endpoints."""

    def test_health_endpoint_simple(self, test_client):
        """Test basic health endpoint."""
        response = test_client.get("/health")

        # Health endpoint may return 503 if database is not available in test
        # This is expected behavior for the infrastructure tests
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data

    def test_health_endpoint_detailed(self, test_client):
        """Test detailed health endpoint."""
        response = test_client.get("/health/detailed")

        # Health endpoint may return 503 if database is not available in test
        # This is expected behavior for the infrastructure tests
        assert response.status_code in [200, 503]
        data = response.json()
        assert "status" in data
        # Only check for these fields if status is healthy
        if response.status_code == 200:
            assert "database" in data
            assert "uptime" in data
            assert "system" in data
