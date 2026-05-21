# file: backend/tests/unit/test_dev_bottlenecks.py
"""Unit tests for the DEV bottleneck hotfix.

Covers:
  - B1: get_logs() device filter now uses the indexed ``device_name``
        column instead of an unindexable ``device.ilike('%"name":...%')``.
  - B2: get_available_profiles() now caches its result for 5 minutes.
"""

from datetime import datetime, timezone

import pytest

import models
from models import (
    DNSLog,
    get_available_profiles,
    get_logs,
    invalidate_profiles_cache,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# B1 — device filter uses device_name column
# ---------------------------------------------------------------------------


def _insert(session, **overrides):
    """Insert a minimal DNSLog row, allowing overrides."""
    defaults = dict(
        timestamp=datetime.now(timezone.utc),
        domain="example.com",
        action="allowed",
        blocked=False,
        profile_id="p1",
        tld="example.com",
        client_ip="10.0.0.1",
        query_type="A",
        device='{"name": "Alice iPhone", "id": "d1"}',
        device_name="Alice iPhone",
        data="{}",
    )
    defaults.update(overrides)
    session.add(DNSLog(**defaults))
    session.commit()


class TestDeviceFilterUsesDeviceNameColumn:
    """The hotfix replaces a JSON-substring scan with a column equality."""

    def test_match_by_exact_device_name(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, device_name="Alice iPhone")
        _insert(test_db, device_name="Bob iPad")

        rows, total = get_logs(time_range="all", device_filter=["Alice iPhone"])

        assert total == 1
        assert rows[0]["device"]["name"] == "Alice iPhone"

    def test_match_multiple_devices(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, device_name="Alice iPhone")
        _insert(test_db, device_name="Bob iPad")
        _insert(test_db, device_name="Charlie Mac")

        _rows, total = get_logs(
            time_range="all", device_filter=["Alice iPhone", "Bob iPad"]
        )

        assert total == 2

    def test_whitespace_only_devices_are_ignored(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, device_name="Alice iPhone")
        _insert(test_db, device_name="Bob iPad")

        # Whitespace-only entries are filtered out; remaining list becomes
        # empty, so no device filter is applied at all → returns both rows.
        # With no filters set, get_logs falls back to the pg_class
        # reltuples estimate (a no-op on SQLite → 0), so we just check
        # the data rows came back uncountstrained.
        rows, _total = get_logs(time_range="all", device_filter=["", "  "])

        assert len(rows) == 2


# ---------------------------------------------------------------------------
# B2 — get_available_profiles is cached
# ---------------------------------------------------------------------------


class TestAvailableProfilesCache:
    """The /profiles result is cached for 5 minutes to avoid a full-table
    aggregate on every page load."""

    def setup_method(self):
        invalidate_profiles_cache()

    def teardown_method(self):
        invalidate_profiles_cache()

    def test_second_call_hits_cache(self, test_db, monkeypatch):
        """A second call must not re-run the DB aggregate."""
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, profile_id="p1")

        first = get_available_profiles()
        # Break the DB so any real query would fail
        monkeypatch.setattr(
            models, "session_factory", lambda: (_ for _ in ()).throw(RuntimeError())
        )

        second = get_available_profiles()
        assert second == first

    def test_invalidate_forces_refresh(self, test_db, monkeypatch):
        """invalidate_profiles_cache() must cause the next call to re-query."""
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, profile_id="p1")

        get_available_profiles()  # prime cache
        invalidate_profiles_cache()

        # Insert a second profile after invalidation — should appear next call
        _insert(test_db, profile_id="p2")
        profiles = get_available_profiles()
        ids = {p["profile_id"] for p in profiles}
        assert ids == {"p1", "p2"}
