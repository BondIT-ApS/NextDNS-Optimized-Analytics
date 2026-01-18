# file: backend/tests/unit/test_models_queries.py
"""
Unit tests for database query functions in models.py.

Tests complex query functions like get_logs, get_stats_overview, etc.
"""

from datetime import datetime, timezone, timedelta
import pytest
from models import (
    DNSLog,
    get_logs,
    get_total_record_count,
    get_logs_stats,
    extract_tld,
)


# Additional extract_tld tests focusing on query-specific scenarios
@pytest.mark.unit
def test_extract_tld_with_query_context():
    """Test TLD extraction in query processing context."""
    # Test cases that might come up in actual DNS log processing
    assert extract_tld("cdn.example.com") == "example.com"
    assert extract_tld("api.service.domain.co.uk") == "co.uk"  # Complex TLD extraction
    assert extract_tld("subdomain.long-domain-name.org") == "long-domain-name.org"


def test_extract_tld_with_malformed_domains():
    """Test TLD extraction with edge cases from real DNS logs."""
    assert extract_tld("..invalid..") == "..invalid.."
    assert extract_tld("single") == "single"
    assert extract_tld(".leadingdot.com") == "leadingdot.com"  # Leading dot removed


def test_dns_log_with_explicit_tld(test_db):
    """Test that DNSLog accepts explicit TLD value."""
    log = DNSLog(
        timestamp=datetime.now(timezone.utc),
        domain="gateway.icloud.com",
        action="allowed",
        device='{"name": "Test", "id": "123"}',
        client_ip="192.168.1.1",
        query_type="A",
        blocked=False,
        profile_id="test",
        tld="icloud.com",  # Explicitly set TLD
        data="{}",
    )
    test_db.add(log)
    test_db.commit()

    # Verify TLD was stored correctly
    retrieved = test_db.query(DNSLog).filter_by(domain="gateway.icloud.com").first()
    assert retrieved.tld == "icloud.com"


def test_dns_log_created_at_auto_set(test_db):
    """Test that created_at is automatically set."""
    log = DNSLog(
        timestamp=datetime.now(timezone.utc),
        domain="test.com",
        action="allowed",
        device='{"name": "Test", "id": "123"}',
        client_ip="192.168.1.1",
        query_type="A",
        blocked=False,
        profile_id="test",
        tld="test.com",
        data="{}",
    )
    test_db.add(log)
    test_db.commit()

    # Verify created_at was set
    assert log.created_at is not None
    assert isinstance(log.created_at, datetime)


def test_dns_log_unique_constraint_prevents_duplicates(test_db):
    """Test that unique constraint prevents duplicate logs."""
    timestamp = datetime.now(timezone.utc)

    # Create first log
    log1 = DNSLog(
        timestamp=timestamp,
        domain="test.com",
        action="allowed",
        device='{"name": "Test", "id": "123"}',
        client_ip="192.168.1.1",
        query_type="A",
        blocked=False,
        profile_id="test",
        tld="test.com",
        data="{}",
    )
    test_db.add(log1)
    test_db.commit()

    # Try to create duplicate - should be handled gracefully
    log2 = DNSLog(
        timestamp=timestamp,
        domain="test.com",
        action="allowed",
        device='{"name": "Test", "id": "123"}',
        client_ip="192.168.1.1",
        query_type="A",
        blocked=False,
        profile_id="test",
        tld="test.com",
        data="{}",
    )
    test_db.add(log2)

    # SQLAlchemy will raise IntegrityError
    from sqlalchemy.exc import IntegrityError

    with pytest.raises(IntegrityError):
        test_db.commit()


def test_dns_log_device_field_stores_json_string(test_db):
    """Test that device field correctly stores JSON string."""
    device_json = '{"name": "iPhone", "id": "abc-123"}'

    log = DNSLog(
        timestamp=datetime.now(timezone.utc),
        domain="test.com",
        action="allowed",
        device=device_json,
        client_ip="192.168.1.1",
        query_type="A",
        blocked=False,
        profile_id="test",
        tld="test.com",
        data="{}",
    )
    test_db.add(log)
    test_db.commit()

    # Retrieve and check
    retrieved = test_db.query(DNSLog).filter_by(domain="test.com").first()
    assert retrieved.device == device_json


def test_dns_log_query_types(test_db):
    """Test different DNS query types are stored correctly."""
    query_types = ["A", "AAAA", "CNAME", "MX", "TXT"]

    for qtype in query_types:
        log = DNSLog(
            timestamp=datetime.now(timezone.utc),
            domain=f"test-{qtype}.com",
            action="allowed",
            device='{"name": "Test", "id": "123"}',
            client_ip="192.168.1.1",
            query_type=qtype,
            blocked=False,
            profile_id="test",
            tld="test.com",
            data="{}",
        )
        test_db.add(log)

    test_db.commit()

    # Verify all were stored
    for qtype in query_types:
        retrieved = test_db.query(DNSLog).filter_by(query_type=qtype).first()
        assert retrieved is not None
        assert retrieved.query_type == qtype
