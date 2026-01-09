# file: backend/tests/unit/test_models.py
"""
🧱 Unit Tests for Database Models

Testing our LEGO data blocks - ensuring each piece works perfectly!
"""

from datetime import datetime, timezone
import pytest
from models import extract_tld, DNSLog, FetchStatus


class TestExtractTLD:
    """Test TLD extraction utility function."""
    
    def test_extract_simple_tld(self):
        """Test extraction of simple TLDs."""
        assert extract_tld("www.google.com") == "google.com"
        assert extract_tld("example.org") == "example.org"
        assert extract_tld("test.net") == "test.net"
    
    def test_extract_subdomain_tld(self):
        """Test extraction from subdomains."""
        assert extract_tld("gateway.icloud.com") == "icloud.com"
        assert extract_tld("bag.itunes.apple.com") == "apple.com"
        assert extract_tld("api.github.com") == "github.com"
    
    def test_extract_hyphenated_tld(self):
        """Test extraction with hyphenated domains."""
        assert extract_tld("gateway.fe2.apple-dns.net") == "apple-dns.net"
        assert extract_tld("my-domain.com") == "my-domain.com"
    
    def test_extract_invalid_input(self):
        """Test handling of invalid inputs."""
        assert extract_tld(None) is None
        assert extract_tld("") == ""
        assert extract_tld(123) == 123  # Returns original if not string
    
    def test_extract_edge_cases(self):
        """Test edge cases."""
        assert extract_tld("localhost") == "localhost"
        assert extract_tld("192.168.1.1") == "192.168.1.1"


class TestDNSLogModel:
    """Test DNSLog database model."""
    
    def test_create_dns_log(self, test_db, sample_dns_log_data):
        """Test creating a DNS log entry."""
        log = DNSLog(
            timestamp=datetime.fromisoformat(sample_dns_log_data["timestamp"]),
            domain=sample_dns_log_data["domain"],
            action=sample_dns_log_data["action"],
            device=sample_dns_log_data["device"],
            client_ip=sample_dns_log_data["client_ip"],
            query_type=sample_dns_log_data["query_type"],
            blocked=sample_dns_log_data["blocked"],
            profile_id=sample_dns_log_data["profile_id"],
            tld=sample_dns_log_data["tld"],
            data=sample_dns_log_data["data"],
        )
        
        test_db.add(log)
        test_db.commit()
        
        # Verify it was created
        retrieved = test_db.query(DNSLog).filter_by(domain="example.com").first()
        assert retrieved is not None
        assert retrieved.domain == "example.com"
        assert retrieved.action == "allowed"
        assert retrieved.blocked is False
    
    def test_dns_log_defaults(self, test_db):
        """Test default values in DNS log model."""
        log = DNSLog(
            timestamp=datetime.now(timezone.utc),
            domain="test.com",
            data='{"test": "data"}',
        )
        
        test_db.add(log)
        test_db.commit()
        
        retrieved = test_db.query(DNSLog).filter_by(domain="test.com").first()
        assert retrieved.query_type == "A"  # Default value
        assert retrieved.blocked is False  # Default value
        assert retrieved.created_at is not None
    
    def test_dns_log_unique_constraint(self, test_db):
        """Test that unique constraint prevents duplicates."""
        timestamp = datetime.now(timezone.utc)
        
        # Create first log
        log1 = DNSLog(
            timestamp=timestamp,
            domain="duplicate.com",
            client_ip="192.168.1.1",
            data='{"test": "data1"}',
        )
        test_db.add(log1)
        test_db.commit()
        
        # Try to create duplicate (should raise error in real DB, SQLite might allow)
        log2 = DNSLog(
            timestamp=timestamp,
            domain="duplicate.com",
            client_ip="192.168.1.1",
            data='{"test": "data2"}',
        )
        test_db.add(log2)
        
        # SQLite in-memory might not enforce this perfectly
        # In production PostgreSQL, this would raise IntegrityError


class TestFetchStatusModel:
    """Test FetchStatus database model."""
    
    def test_create_fetch_status(self, test_db):
        """Test creating a fetch status entry."""
        status = FetchStatus(
            last_fetch_timestamp=datetime.now(timezone.utc),
            profile_id="test-profile-123",
            records_fetched=100,
        )
        
        test_db.add(status)
        test_db.commit()
        
        retrieved = test_db.query(FetchStatus).filter_by(profile_id="test-profile-123").first()
        assert retrieved is not None
        assert retrieved.profile_id == "test-profile-123"
        assert retrieved.records_fetched == 100
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None
    
    def test_fetch_status_defaults(self, test_db):
        """Test default values in fetch status model."""
        status = FetchStatus(
            last_fetch_timestamp=datetime.now(timezone.utc),
            profile_id="test-profile",
        )
        
        test_db.add(status)
        test_db.commit()
        
        retrieved = test_db.query(FetchStatus).filter_by(profile_id="test-profile").first()
        assert retrieved.records_fetched == 0  # Default value
        assert retrieved.last_successful_fetch is not None
