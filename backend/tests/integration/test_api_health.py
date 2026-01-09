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

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_health_endpoint_detailed(self, test_client):
        """Test detailed health endpoint."""
        response = test_client.get("/health/detailed")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "uptime" in data
        assert "system" in data
