# file: backend/tests/integration/test_api_stats.py
"""
Integration tests for statistics API endpoints.

Tests the /stats/* endpoints including overview, timeseries, domains, TLDs, and devices.
"""

import pytest
from fastapi import status

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.integration
def test_get_stats_overview(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/overview returns overview statistics."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/overview")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_queries" in data
    assert "blocked_queries" in data
    assert "allowed_queries" in data
    assert "blocked_percentage" in data
    assert "queries_per_hour" in data
    assert isinstance(data["total_queries"], int)
    assert isinstance(data["blocked_queries"], int)
    assert isinstance(data["allowed_queries"], int)


@pytest.mark.integration
def test_get_stats_overview_with_time_range(
    test_client, populated_test_db, monkeypatch
):
    """Test GET /stats/overview with time range filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/overview?time_range=24h")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_queries" in data


@pytest.mark.integration
def test_get_stats_overview_with_profile(
    test_client, populated_test_db, monkeypatch
):
    """Test GET /stats/overview with profile filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/overview?profile=test-profile")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_queries" in data


@pytest.mark.integration
def test_get_stats_timeseries(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/timeseries returns time series data."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/timeseries")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "granularity" in data
    assert "total_points" in data
    assert isinstance(data["data"], list)


@pytest.mark.integration
def test_get_stats_timeseries_with_time_range(
    test_client, populated_test_db, monkeypatch
):
    """Test GET /stats/timeseries with different time ranges."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/timeseries?time_range=24h")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "granularity" in data


@pytest.mark.integration
def test_get_stats_domains(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/domains returns top domains."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/domains")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "blocked_domains" in data
    assert "allowed_domains" in data
    assert isinstance(data["blocked_domains"], list)
    assert isinstance(data["allowed_domains"], list)


@pytest.mark.integration
def test_get_stats_domains_with_limit(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/domains with limit parameter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/domains?limit=5")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["blocked_domains"]) <= 5
    assert len(data["allowed_domains"]) <= 5


@pytest.mark.integration
def test_get_stats_tlds(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/tlds returns TLD statistics."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/tlds")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "blocked_tlds" in data
    assert "allowed_tlds" in data
    assert isinstance(data["blocked_tlds"], list)
    assert isinstance(data["allowed_tlds"], list)


@pytest.mark.integration
def test_get_devices_list(test_client, populated_test_db, monkeypatch):
    """Test GET /devices returns device information."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/devices")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # Can be either list or dict depending on endpoint implementation
    assert isinstance(data, (list, dict))


@pytest.mark.integration
def test_get_stats_devices(test_client, populated_test_db, monkeypatch):
    """Test GET /stats/devices returns device statistics."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats/devices")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "devices" in data
    assert isinstance(data["devices"], list)


@pytest.mark.integration
def test_get_stats_endpoint(test_client, populated_test_db, monkeypatch):
    """Test GET /stats returns database statistics."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient

    client = TestClient(app)

    response = client.get("/stats")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total_records" in data
    assert "message" in data
    assert isinstance(data["total_records"], int)
    assert isinstance(data["message"], str)
