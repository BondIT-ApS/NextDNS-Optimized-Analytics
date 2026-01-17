# file: backend/tests/integration/test_api_logs.py
"""
Integration tests for logs API endpoints.

Tests the /logs and /logs/stats endpoints with various filters.
"""

import pytest
from fastapi import status

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.mark.integration
def test_get_logs_basic(test_client, populated_test_db, monkeypatch):
    """Test GET /logs returns logs successfully."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "total_records" in data
    assert "returned_records" in data
    assert isinstance(data["data"], list)
    assert data["total_records"] >= 0
    assert data["returned_records"] >= 0


@pytest.mark.integration
def test_get_logs_with_limit(test_client, populated_test_db, monkeypatch):
    """Test GET /logs respects limit parameter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?limit=5")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data["data"]) <= 5
    assert data["returned_records"] <= 5


@pytest.mark.integration
def test_get_logs_with_offset(test_client, populated_test_db, monkeypatch):
    """Test GET /logs respects offset parameter for pagination."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?limit=5&offset=2")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data


@pytest.mark.integration
def test_get_logs_with_search(test_client, populated_test_db, monkeypatch):
    """Test GET /logs with search parameter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?search=test")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data


@pytest.mark.integration
def test_get_logs_with_status_filter(test_client, populated_test_db, monkeypatch):
    """Test GET /logs with status filter (blocked/allowed)."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?status_filter=blocked")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data


@pytest.mark.integration
def test_get_logs_with_profile_filter(test_client, populated_test_db, monkeypatch):
    """Test GET /logs with profile filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?profile=test-profile")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data


@pytest.mark.integration
def test_get_logs_with_time_range(test_client, populated_test_db, monkeypatch):
    """Test GET /logs with time range filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?time_range=24h")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data


@pytest.mark.integration
def test_get_logs_with_exclude_domains(test_client, populated_test_db, monkeypatch):
    """Test GET /logs with domain exclusion."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs?exclude=test0.example.com&exclude=test1.example.com")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "excluded_domains" in data
    assert isinstance(data["excluded_domains"], list)


@pytest.mark.integration
def test_get_logs_stats_basic(test_client, populated_test_db, monkeypatch):
    """Test GET /logs/stats returns statistics."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs/stats")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "blocked" in data
    assert "allowed" in data
    assert "blocked_percentage" in data
    assert "allowed_percentage" in data
    assert isinstance(data["total"], int)
    assert isinstance(data["blocked"], int)
    assert isinstance(data["allowed"], int)


@pytest.mark.integration
def test_get_logs_stats_with_profile(test_client, populated_test_db, monkeypatch):
    """Test GET /logs/stats with profile filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs/stats?profile=test-profile")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "profile_id" in data


@pytest.mark.integration
def test_get_logs_stats_with_time_range(test_client, populated_test_db, monkeypatch):
    """Test GET /logs/stats with time range filter."""
    monkeypatch.setenv("AUTH_ENABLED", "false")

    from main import app
    from fastapi.testclient import TestClient
    client = TestClient(app)

    response = client.get("/logs/stats?time_range=7d")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "total" in data
    assert "blocked" in data
    assert "allowed" in data


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
