# file: backend/tests/unit/test_wildcard_exclusion.py
"""Unit tests for wildcard domain exclusion functionality."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, DNSLog, build_domain_exclusion_filter
from datetime import datetime, timezone


@pytest.fixture
def in_memory_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Add test data
    test_domains = [
        "gateway.icloud.com",
        "www.apple.com",
        "tracking.google.com",
        "ads.example.com",
        "api.tracking.net",
        "facebook.com",
        "analytics.facebook.com",
        "youtube.com",
        "google.com",
        "amazon.com",
    ]

    for i, domain in enumerate(test_domains):
        log = DNSLog(
            timestamp=datetime.now(timezone.utc),
            domain=domain,
            action="allowed",
            device='{"name": "test-device"}',
            client_ip=f"192.168.1.{i}",
            query_type="A",
            blocked=False,
            profile_id="test_profile",
            data="{}",
        )
        session.add(log)

    session.commit()
    yield session
    session.close()


@pytest.mark.unit
class TestWildcardPatternMatching:
    """Test wildcard pattern matching in domain exclusion."""

    def test_leading_wildcard_excludes_subdomains(self, in_memory_db):
        """Test that *.apple.com excludes all apple.com subdomains."""
        session = in_memory_db
        exclude_patterns = ["*.apple.com"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude gateway.icloud.com and www.apple.com
        assert "www.apple.com" not in results
        # Should NOT exclude exact match (apple.com not in test data)
        # Should include other domains
        assert "gateway.icloud.com" in results
        assert "facebook.com" in results
        assert len(results) == 9  # 10 total - 1 excluded

    def test_trailing_wildcard_excludes_tlds(self, in_memory_db):
        """Test that tracking.* excludes all tracking.* domains."""
        session = in_memory_db
        exclude_patterns = ["tracking.*"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude tracking.google.com and api.tracking.net
        assert "tracking.google.com" not in results
        # Should include domains not matching pattern
        assert "facebook.com" in results
        assert "youtube.com" in results
        assert len(results) == 9  # 10 total - 1 excluded (only tracking.google.com)

    def test_middle_wildcard_excludes_containing(self, in_memory_db):
        """Test that *tracking* excludes domains containing 'tracking'."""
        session = in_memory_db
        exclude_patterns = ["*tracking*"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude tracking.google.com and api.tracking.net
        assert "tracking.google.com" not in results
        assert "api.tracking.net" not in results
        # Should include others
        assert "facebook.com" in results
        assert len(results) == 8  # 10 total - 2 excluded

    def test_exact_match_exclusion(self, in_memory_db):
        """Test that exact domain matches are excluded (no wildcard)."""
        session = in_memory_db
        exclude_patterns = ["facebook.com", "youtube.com"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude exact matches
        assert "facebook.com" not in results
        assert "youtube.com" not in results
        # Should NOT exclude subdomains
        assert "analytics.facebook.com" in results
        assert len(results) == 8  # 10 total - 2 excluded

    def test_mixed_exact_and_wildcard(self, in_memory_db):
        """Test combination of exact matches and wildcard patterns."""
        session = in_memory_db
        exclude_patterns = ["facebook.com", "*.apple.com", "*tracking*"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude:
        # - facebook.com (exact)
        # - www.apple.com (*.apple.com wildcard)
        # - tracking.google.com and api.tracking.net (*tracking*)
        assert "facebook.com" not in results
        assert "www.apple.com" not in results
        assert "tracking.google.com" not in results
        assert "api.tracking.net" not in results
        # Should include others
        assert "analytics.facebook.com" in results
        assert "gateway.icloud.com" in results
        assert "youtube.com" in results
        assert len(results) == 6  # 10 total - 4 excluded

    def test_empty_exclude_list_returns_all(self, in_memory_db):
        """Test that empty exclude list returns all records."""
        session = in_memory_db
        exclude_patterns = []

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        if filter_cond is None:
            query = session.query(DNSLog)
        else:
            query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        assert len(results) == 10  # All records

    def test_none_exclude_list_returns_all(self, in_memory_db):
        """Test that None exclude list returns all records."""
        session = in_memory_db
        exclude_patterns = None

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        if filter_cond is None:
            query = session.query(DNSLog)
        else:
            query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        assert len(results) == 10  # All records

    def test_overly_broad_wildcards_rejected(self, in_memory_db):
        """Test that overly broad wildcards like * or *.* are rejected."""
        session = in_memory_db
        exclude_patterns = ["*", "*.*", "**"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        if filter_cond is None:
            query = session.query(DNSLog)
        else:
            query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should not exclude anything (patterns rejected)
        assert len(results) == 10

    def test_case_insensitive_wildcard_matching(self, in_memory_db):
        """Test that wildcard patterns work case-insensitively."""
        session = in_memory_db
        exclude_patterns = ["*.APPLE.COM", "FACEBOOK.com"]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude despite case differences
        # Note: This depends on database collation (SQLite is case-insensitive by default)
        assert "www.apple.com" not in results
        assert "facebook.com" not in results

    def test_special_characters_escaped(self, in_memory_db):
        """Test that SQL LIKE special characters are properly escaped."""
        session = in_memory_db
        # Add domain with underscore
        log = DNSLog(
            timestamp=datetime.now(timezone.utc),
            domain="test_domain.com",
            action="allowed",
            device='{"name": "test"}',
            client_ip="192.168.1.100",
            query_type="A",
            blocked=False,
            profile_id="test_profile",
            data="{}",
        )
        session.add(log)
        session.commit()

        exclude_patterns = ["test_domain.com"]  # Exact match with underscore
        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude exact match
        assert "test_domain.com" not in results
        # Should still have original 10
        assert len(results) == 10


@pytest.mark.unit
class TestWildcardEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_string_in_patterns(self, in_memory_db):
        """Test that empty strings in pattern list are ignored."""
        session = in_memory_db
        exclude_patterns = ["", "  ", "facebook.com", ""]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should only exclude facebook.com
        assert "facebook.com" not in results
        assert len(results) == 9

    def test_none_values_in_patterns(self, in_memory_db):
        """Test that None values in pattern list are ignored."""
        session = in_memory_db
        exclude_patterns = [None, "facebook.com", None]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should only exclude facebook.com
        assert "facebook.com" not in results
        assert len(results) == 9

    def test_whitespace_trimmed(self, in_memory_db):
        """Test that whitespace is trimmed from patterns."""
        session = in_memory_db
        exclude_patterns = ["  facebook.com  ", " *.apple.com "]

        filter_cond = build_domain_exclusion_filter(DNSLog.domain, exclude_patterns)
        query = session.query(DNSLog).filter(filter_cond)
        results = [log.domain for log in query.all()]

        # Should exclude after trimming whitespace
        assert "facebook.com" not in results
        assert "www.apple.com" not in results
        assert len(results) == 8


@pytest.mark.unit
def test_build_domain_exclusion_filter_returns_none_for_empty():
    """Test that build_domain_exclusion_filter returns None for empty lists."""
    filter_cond = build_domain_exclusion_filter(DNSLog.domain, [])
    assert filter_cond is None

    filter_cond = build_domain_exclusion_filter(DNSLog.domain, None)
    assert filter_cond is None
