# file: backend/tests/conftest.py
"""
🧱 LEGO Test Configuration - pytest fixtures and setup

Shared test fixtures for the NextDNS Optimized Analytics backend tests.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add backend directory to Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models import Base, DNSLog, FetchStatus  # pylint: disable=wrong-import-position


@pytest.fixture(scope="function")
def test_db():
    """
    Create an in-memory SQLite database for testing.

    Each test gets a fresh database that is automatically cleaned up.
    """
    # Create in-memory database
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    # Create all tables
    Base.metadata.create_all(engine)

    # Create session factory
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture(scope="function")
def test_client(test_db):
    """
    Create a FastAPI test client with a test database session.

    This fixture provides a test client for making API requests.
    """
    from main import app  # pylint: disable=import-outside-toplevel

    # Override database dependency if needed
    # For now, just return a basic test client
    client = TestClient(app)

    yield client


@pytest.fixture
def sample_dns_log_data():
    """
    Sample DNS log data for testing.

    Returns a dictionary representing a typical DNS log entry.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": "example.com",
        "action": "allowed",
        "device": '{"name": "Test Device", "id": "device-123"}',
        "client_ip": "192.168.1.100",
        "query_type": "A",
        "blocked": False,
        "profile_id": "test-profile",
        "tld": "example.com",
        "data": '{"meta": "test data"}',
    }


@pytest.fixture
def sample_blocked_log_data():
    """
    Sample blocked DNS log data for testing.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "domain": "malicious.com",
        "action": "blocked",
        "device": '{"name": "Test Device", "id": "device-123"}',
        "client_ip": "192.168.1.100",
        "query_type": "A",
        "blocked": True,
        "profile_id": "test-profile",
        "tld": "malicious.com",
        "data": '{"meta": "blocked"}',
    }


@pytest.fixture
def mock_nextdns_response():
    """
    Mock NextDNS API response for testing.

    Returns a typical response structure from NextDNS API.
    """
    return {
        "data": [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "domain": "example.com",
                "type": "A",
                "status": "allowed",
                "device": {"id": "device-1", "name": "Test Device"},
                "clientIp": "192.168.1.100",
            },
            {
                "timestamp": (
                    datetime.now(timezone.utc) - timedelta(hours=1)
                ).isoformat(),
                "domain": "tracking.com",
                "type": "A",
                "status": "blocked",
                "device": {"id": "device-1", "name": "Test Device"},
                "clientIp": "192.168.1.100",
            },
        ],
        "meta": {"pagination": {"cursor": "next-page-token"}},
    }


@pytest.fixture
def populated_test_db(test_db):
    """
    Create a test database with sample DNS logs.

    Useful for integration tests that need existing data.
    """
    # Insert sample data
    base_time = datetime.now(timezone.utc) - timedelta(days=1)

    for i in range(10):
        log = DNSLog(
            timestamp=base_time + timedelta(hours=i),
            domain=f"test{i}.example.com",
            action="allowed" if i % 2 == 0 else "blocked",
            device='{"name": "Test Device", "id": "device-123"}',
            client_ip="192.168.1.100",
            query_type="A",
            blocked=i % 2 != 0,
            profile_id="test-profile",
            tld="example.com",
            data=f'{{"index": {i}}}',
        )
        test_db.add(log)

    test_db.commit()

    yield test_db


@pytest.fixture
def api_key():
    """
    Test API key for authentication tests.
    """
    return "test-api-key-123"


@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Mock environment variables for testing.

    Automatically applied to all tests.
    """
    monkeypatch.setenv("LOCAL_API_KEY", "test-api-key-123")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_password")
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
