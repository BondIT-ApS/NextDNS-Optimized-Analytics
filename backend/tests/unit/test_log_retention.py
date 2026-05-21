# file: backend/tests/unit/test_log_retention.py
"""Unit tests for the log retention setting + nightly cleanup."""

from datetime import datetime, timezone, timedelta

import pytest

import models
from models import (
    DNSLog,
    RETENTION_MIN_DAYS,
    delete_logs_older_than,
    get_retention_days,
    set_retention_days,
)

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Setting getter / setter
# ---------------------------------------------------------------------------


class TestRetentionSetting:
    def test_default_is_unlimited(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        assert get_retention_days() == 0

    def test_set_and_get_roundtrip(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        set_retention_days(90)
        assert get_retention_days() == 90

    def test_zero_means_unlimited(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        set_retention_days(60)
        set_retention_days(0)
        assert get_retention_days() == 0

    def test_negative_values_clamped_to_zero(self, test_db, monkeypatch):
        # The model layer is permissive; API layer enforces bounds.
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        set_retention_days(-5)
        assert get_retention_days() == 0

    def test_min_days_constant(self):
        # Locked into the public API so the frontend can rely on it.
        assert RETENTION_MIN_DAYS == 30


# ---------------------------------------------------------------------------
# delete_logs_older_than()
# ---------------------------------------------------------------------------


def _insert(session, timestamp, **overrides):
    defaults = dict(
        timestamp=timestamp,
        domain="example.com",
        action="allowed",
        blocked=False,
        profile_id="p1",
        tld="example.com",
        client_ip="10.0.0.1",
        query_type="A",
        device='{"name": "x"}',
        device_name="x",
        data="{}",
    )
    defaults.update(overrides)
    session.add(DNSLog(**defaults))
    session.commit()


class TestDeleteLogsOlderThan:
    def test_zero_is_noop(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, datetime.now(timezone.utc) - timedelta(days=400))

        deleted = delete_logs_older_than(0)

        assert deleted == 0
        assert test_db.query(DNSLog).count() == 1

    def test_negative_is_noop(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, datetime.now(timezone.utc) - timedelta(days=400))

        assert delete_logs_older_than(-1) == 0
        assert test_db.query(DNSLog).count() == 1

    def test_only_old_rows_are_deleted(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        now = datetime.now(timezone.utc)
        # 5 rows older than 30 days, 3 rows newer
        for i in range(5):
            _insert(test_db, now - timedelta(days=31 + i))
        for i in range(3):
            _insert(test_db, now - timedelta(days=i))

        deleted = delete_logs_older_than(30)

        assert deleted == 5
        assert test_db.query(DNSLog).count() == 3

    def test_batching_processes_all_rows(self, test_db, monkeypatch):
        """With a tiny batch size, we should still delete every old row."""
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        now = datetime.now(timezone.utc)
        for i in range(12):
            _insert(test_db, now - timedelta(days=40 + i))

        deleted = delete_logs_older_than(30, batch_size=4)

        assert deleted == 12
        assert test_db.query(DNSLog).count() == 0

    def test_no_old_rows_no_deletes(self, test_db, monkeypatch):
        monkeypatch.setattr(models, "session_factory", lambda: test_db)
        _insert(test_db, datetime.now(timezone.utc))

        deleted = delete_logs_older_than(30)

        assert deleted == 0
        assert test_db.query(DNSLog).count() == 1
