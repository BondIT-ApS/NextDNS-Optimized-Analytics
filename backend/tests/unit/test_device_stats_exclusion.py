# file: backend/tests/unit/test_device_stats_exclusion.py
"""Unit tests for device statistics with domain exclusion."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
from models import get_stats_devices, Base, DNSLog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def device_stats_db():
    """Create an in-memory database with device-specific test data."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Create test data with multiple devices and domains
    test_data = [
        # iPhone device - 10 queries total (5 blocked, 5 allowed)
        ("iPhone", "gateway.icloud.com", False),
        ("iPhone", "www.apple.com", False),
        ("iPhone", "ads.example.com", True),
        ("iPhone", "tracking.google.com", True),
        ("iPhone", "api.tracking.net", True),
        ("iPhone", "facebook.com", False),
        ("iPhone", "analytics.facebook.com", True),
        ("iPhone", "youtube.com", False),
        ("iPhone", "google.com", False),
        ("iPhone", "amazon.com", True),
        # MacBook device - 8 queries total (3 blocked, 5 allowed)
        ("MacBook", "gateway.icloud.com", False),
        ("MacBook", "www.apple.com", False),
        ("MacBook", "ads.example.com", True),
        ("MacBook", "github.com", False),
        ("MacBook", "stackoverflow.com", False),
        ("MacBook", "tracking.google.com", True),
        ("MacBook", "reddit.com", False),
        ("MacBook", "api.tracking.net", True),
        # Router device - 5 queries total (2 blocked, 3 allowed)
        ("Router", "dns.google.com", False),
        ("Router", "cloudflare.com", False),
        ("Router", "ads.example.com", True),
        ("Router", "tracking.google.com", True),
        ("Router", "amazon.com", False),
    ]

    for i, (device_name, domain, blocked) in enumerate(test_data):
        log = DNSLog(
            timestamp=datetime.now(timezone.utc),
            domain=domain,
            action="blocked" if blocked else "allowed",
            device=f'{{"name": "{device_name}"}}',
            client_ip=f"192.168.1.{i % 255}",
            query_type="A",
            blocked=blocked,
            profile_id="test_profile",
            data="{}",
        )
        session.add(log)

    session.commit()
    yield engine
    session.close()


@pytest.mark.unit
class TestDeviceStatsWithDomainExclusion:
    """Test device statistics calculations with domain exclusion."""

    @patch("models.session_factory")
    def test_device_stats_exclude_wildcard_domains(
        self, mock_session_factory, device_stats_db
    ):
        """Test that device stats correctly exclude wildcard domain patterns."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude all Apple domains (*.apple.com, gateway.icloud.com)
        exclude_domains = ["*.apple.com", "gateway.icloud.com"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=exclude_domains,
        )

        # iPhone should have 8 queries (10 total - 2 apple domains)
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats is not None
        assert iphone_stats["total_queries"] == 8
        assert iphone_stats["blocked_queries"] == 5  # No apple domains were blocked
        assert iphone_stats["allowed_queries"] == 3  # 5 - 2 excluded

        # MacBook should have 6 queries (8 total - 2 apple domains)
        macbook_stats = next(
            (d for d in results if d["device_name"] == "MacBook"), None
        )
        assert macbook_stats is not None
        assert macbook_stats["total_queries"] == 6
        assert macbook_stats["blocked_queries"] == 3
        assert macbook_stats["allowed_queries"] == 3  # 5 - 2 excluded

    @patch("models.session_factory")
    def test_device_stats_exclude_tracking_domains(
        self, mock_session_factory, device_stats_db
    ):
        """Test excluding tracking-related domains with wildcards."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude all tracking domains (*tracking*)
        exclude_domains = ["*tracking*"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=exclude_domains,
        )

        # iPhone should have 8 queries (10 - 2 tracking domains)
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats is not None
        assert iphone_stats["total_queries"] == 8
        # tracking.google.com (blocked) and api.tracking.net (blocked) excluded
        assert iphone_stats["blocked_queries"] == 3  # 5 - 2 tracking
        assert iphone_stats["allowed_queries"] == 5

        # MacBook should have 6 queries (8 - 2 tracking)
        macbook_stats = next(
            (d for d in results if d["device_name"] == "MacBook"), None
        )
        assert macbook_stats is not None
        assert macbook_stats["total_queries"] == 6
        assert macbook_stats["blocked_queries"] == 1  # 3 - 2 tracking
        assert macbook_stats["allowed_queries"] == 5

        # Router should have 4 queries (5 - 1 tracking.google.com)
        router_stats = next((d for d in results if d["device_name"] == "Router"), None)
        assert router_stats is not None
        assert router_stats["total_queries"] == 4
        assert router_stats["blocked_queries"] == 1  # 2 - 1 tracking.google.com
        assert router_stats["allowed_queries"] == 3

    @patch("models.session_factory")
    def test_device_stats_exact_domain_exclusion(
        self, mock_session_factory, device_stats_db
    ):
        """Test exact domain match exclusion (no wildcards)."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude specific domains
        exclude_domains = ["facebook.com", "youtube.com", "amazon.com"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=exclude_domains,
        )

        # iPhone should have 7 queries (10 - 3 excluded)
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats is not None
        assert iphone_stats["total_queries"] == 7
        # amazon.com was blocked, facebook/youtube were allowed
        assert iphone_stats["blocked_queries"] == 4  # 5 - 1 (amazon)
        assert iphone_stats["allowed_queries"] == 3  # 5 - 2 (facebook, youtube)

        # Router should have 4 queries (5 - 1 amazon)
        router_stats = next((d for d in results if d["device_name"] == "Router"), None)
        assert router_stats is not None
        assert router_stats["total_queries"] == 4
        assert router_stats["blocked_queries"] == 2  # ads.example, tracking.google
        assert router_stats["allowed_queries"] == 2  # dns.google, cloudflare

    @patch("models.session_factory")
    def test_device_and_domain_exclusion_combined(
        self, mock_session_factory, device_stats_db
    ):
        """Test combining device exclusion with domain exclusion."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude Router device AND tracking domains
        exclude_devices = ["Router"]
        exclude_domains = ["*tracking*"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=exclude_devices,
            exclude_domains=exclude_domains,
        )

        # Should only have iPhone and MacBook
        device_names = [d["device_name"] for d in results]
        assert "Router" not in device_names
        assert "iPhone" in device_names
        assert "MacBook" in device_names
        assert len(results) == 2

        # Verify iPhone stats (8 queries after domain exclusion)
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats["total_queries"] == 8

    @patch("models.session_factory")
    def test_device_stats_no_exclusions(self, mock_session_factory, device_stats_db):
        """Test device stats without any exclusions (baseline)."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=None,
        )

        # Should have all three devices
        assert len(results) == 3

        # iPhone: 10 total (5 blocked, 5 allowed)
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats["total_queries"] == 10
        assert iphone_stats["blocked_queries"] == 5
        assert iphone_stats["allowed_queries"] == 5
        assert iphone_stats["blocked_percentage"] == 50.0

        # MacBook: 8 total (3 blocked, 5 allowed)
        macbook_stats = next(
            (d for d in results if d["device_name"] == "MacBook"), None
        )
        assert macbook_stats["total_queries"] == 8
        assert macbook_stats["blocked_queries"] == 3
        assert macbook_stats["allowed_queries"] == 5
        assert macbook_stats["blocked_percentage"] == pytest.approx(37.5, rel=0.1)

        # Router: 5 total (2 blocked, 3 allowed)
        router_stats = next((d for d in results if d["device_name"] == "Router"), None)
        assert router_stats["total_queries"] == 5
        assert router_stats["blocked_queries"] == 2
        assert router_stats["allowed_queries"] == 3
        assert router_stats["blocked_percentage"] == 40.0

    @patch("models.session_factory")
    def test_device_stats_empty_domain_exclusion_list(
        self, mock_session_factory, device_stats_db
    ):
        """Test that empty domain exclusion list returns all data."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Empty list should be same as no exclusion
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=[],
        )

        assert len(results) == 3
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats["total_queries"] == 10

    @patch("models.session_factory")
    def test_device_stats_blocked_percentage_calculation(
        self, mock_session_factory, device_stats_db
    ):
        """Test that blocked percentage is calculated correctly after exclusion."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude ads.example.com (blocked on all devices)
        exclude_domains = ["ads.example.com"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=exclude_domains,
        )

        # iPhone: 9 total (4 blocked, 5 allowed) after excluding ads.example.com
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats["total_queries"] == 9
        assert iphone_stats["blocked_queries"] == 4  # 5 - 1 (ads)
        assert iphone_stats["allowed_queries"] == 5
        expected_percentage = (4 / 9) * 100
        assert iphone_stats["blocked_percentage"] == pytest.approx(
            expected_percentage, rel=0.1
        )

    @patch("models.session_factory")
    def test_device_stats_multiple_wildcard_patterns(
        self, mock_session_factory, device_stats_db
    ):
        """Test multiple wildcard patterns work together."""
        Session = sessionmaker(bind=device_stats_db)
        mock_session_factory.return_value = Session()

        # Exclude multiple patterns
        exclude_domains = ["*.apple.com", "*tracking*", "ads.example.com"]
        results = get_stats_devices(
            profile_filter="test_profile",
            time_range="all",
            limit=10,
            exclude_devices=None,
            exclude_domains=exclude_domains,
        )

        # iPhone: 10 total - 1 apple - 2 tracking - 1 ads = 6 queries
        # Excluded: www.apple.com, tracking.google.com, api.tracking.net, ads.example.com
        # Remaining: gateway.icloud.com, facebook.com, analytics.facebook.com, youtube.com, google.com, amazon.com
        iphone_stats = next((d for d in results if d["device_name"] == "iPhone"), None)
        assert iphone_stats is not None
        assert iphone_stats["total_queries"] == 6
        assert iphone_stats["blocked_queries"] == 2  # analytics.facebook.com, amazon.com
        assert iphone_stats["allowed_queries"] == 4  # gateway.icloud, facebook, youtube, google
