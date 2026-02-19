# file: backend/tests/unit/test_settings.py
"""
🧱 Unit Tests for NextDNS Settings Models and Helper Functions

Testing the settings LEGO pieces — API key storage, profile management,
and env-var migration logic.
"""

import os
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock

import pytest
from models import SystemSetting, NextDNSProfile, DNSLog, FetchStatus

# Mark all tests in this module as unit tests
pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Model tests (use test_db SQLite fixture directly)
# ---------------------------------------------------------------------------


class TestSystemSettingModel:
    """Test SystemSetting database model."""

    def test_create_setting(self, test_db):
        """Test inserting a key/value setting."""
        setting = SystemSetting(key="nextdns_api_key", value="abc123")
        test_db.add(setting)
        test_db.commit()

        retrieved = (
            test_db.query(SystemSetting).filter_by(key="nextdns_api_key").first()
        )
        assert retrieved is not None
        assert retrieved.value == "abc123"
        assert retrieved.created_at is not None
        assert retrieved.updated_at is not None

    def test_setting_primary_key_uniqueness(self, test_db):
        """Test that inserting the same key twice raises an error."""
        from sqlalchemy.exc import IntegrityError

        test_db.add(SystemSetting(key="dup_key", value="first"))
        test_db.commit()
        test_db.add(SystemSetting(key="dup_key", value="second"))
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()

    def test_setting_nullable_value(self, test_db):
        """Test that value can be None."""
        setting = SystemSetting(key="empty_key", value=None)
        test_db.add(setting)
        test_db.commit()

        retrieved = test_db.query(SystemSetting).filter_by(key="empty_key").first()
        assert retrieved.value is None


class TestNextDNSProfileModel:
    """Test NextDNSProfile database model."""

    def test_create_profile(self, test_db):
        """Test inserting a profile."""
        profile = NextDNSProfile(profile_id="abc123", enabled=True)
        test_db.add(profile)
        test_db.commit()

        retrieved = test_db.query(NextDNSProfile).filter_by(profile_id="abc123").first()
        assert retrieved is not None
        assert retrieved.enabled is True
        assert retrieved.created_at is not None

    def test_profile_defaults_to_enabled(self, test_db):
        """Test that new profiles default to enabled=True."""
        profile = NextDNSProfile(profile_id="def456")
        test_db.add(profile)
        test_db.commit()

        retrieved = test_db.query(NextDNSProfile).filter_by(profile_id="def456").first()
        assert retrieved.enabled is True

    def test_disable_profile(self, test_db):
        """Test disabling a profile."""
        profile = NextDNSProfile(profile_id="ghi789", enabled=True)
        test_db.add(profile)
        test_db.commit()

        profile.enabled = False
        test_db.commit()

        retrieved = test_db.query(NextDNSProfile).filter_by(profile_id="ghi789").first()
        assert retrieved.enabled is False

    def test_profile_primary_key_uniqueness(self, test_db):
        """Test that the same profile_id cannot be inserted twice."""
        from sqlalchemy.exc import IntegrityError

        test_db.add(NextDNSProfile(profile_id="dup"))
        test_db.commit()
        test_db.add(NextDNSProfile(profile_id="dup"))
        with pytest.raises(IntegrityError):
            test_db.commit()
        test_db.rollback()


# ---------------------------------------------------------------------------
# Helper function tests (patch session_factory to use the test SQLite session)
# ---------------------------------------------------------------------------


def _make_session_patcher(test_db):
    """Return a context manager that replaces session_factory with one using test_db."""
    mock_factory = MagicMock(return_value=test_db)
    # Prevent the test session from being closed by the helper functions
    test_db.close = lambda: None
    return patch("models.session_factory", mock_factory)


class TestGetSetSetting:
    """Test get_setting / set_setting helpers."""

    def test_get_missing_key_returns_none(self, test_db):
        """get_setting returns None when key does not exist."""
        from models import get_setting

        with _make_session_patcher(test_db):
            assert get_setting("nonexistent") is None

    def test_set_and_get_setting(self, test_db):
        """set_setting persists a value, get_setting retrieves it."""
        from models import get_setting, set_setting

        with _make_session_patcher(test_db):
            assert set_setting("test_key", "hello") is True
            assert get_setting("test_key") == "hello"

    def test_set_setting_upserts(self, test_db):
        """set_setting updates an existing key."""
        from models import get_setting, set_setting

        with _make_session_patcher(test_db):
            set_setting("update_key", "first")
            set_setting("update_key", "second")
            assert get_setting("update_key") == "second"


class TestApiKeyHelpers:
    """Test get_nextdns_api_key / set_nextdns_api_key helpers."""

    def test_returns_none_when_no_key_no_env(self, test_db, monkeypatch):
        """Returns None when DB is empty and env var is unset."""
        from models import get_nextdns_api_key

        monkeypatch.delenv("API_KEY", raising=False)
        with _make_session_patcher(test_db):
            assert get_nextdns_api_key() is None

    def test_falls_back_to_env_var(self, test_db, monkeypatch):
        """Falls back to API_KEY env var when DB has no entry."""
        from models import get_nextdns_api_key

        monkeypatch.setenv("API_KEY", "env-key-123")
        with _make_session_patcher(test_db):
            assert get_nextdns_api_key() == "env-key-123"

    def test_db_key_takes_priority_over_env(self, test_db, monkeypatch):
        """DB value overrides env var when both are set."""
        from models import get_nextdns_api_key, set_nextdns_api_key

        monkeypatch.setenv("API_KEY", "env-key")
        with _make_session_patcher(test_db):
            set_nextdns_api_key("db-key")
            assert get_nextdns_api_key() == "db-key"

    def test_set_nextdns_api_key_persists(self, test_db):
        """set_nextdns_api_key stores the key in system_settings."""
        from models import set_nextdns_api_key

        with _make_session_patcher(test_db):
            assert set_nextdns_api_key("my-secret-key") is True
            row = test_db.query(SystemSetting).filter_by(key="nextdns_api_key").first()
            assert row is not None
            assert row.value == "my-secret-key"


class TestProfileHelpers:
    """Test profile management helper functions."""

    def test_add_and_get_profile(self, test_db):
        """add_profile inserts, get_profile retrieves."""
        from models import add_profile, get_profile

        with _make_session_patcher(test_db):
            assert add_profile("abc123") is True
            row = get_profile("abc123")
            assert row is not None
            assert row.profile_id == "abc123"
            assert row.enabled is True

    def test_add_duplicate_profile_returns_false(self, test_db):
        """Adding the same profile twice returns False."""
        from models import add_profile

        with _make_session_patcher(test_db):
            assert add_profile("abc123") is True
            assert add_profile("abc123") is False

    def test_get_active_profile_ids_returns_only_enabled(self, test_db):
        """get_active_profile_ids excludes disabled profiles."""
        from models import (
            add_profile,
            update_profile_enabled,
            get_active_profile_ids,
        )

        with _make_session_patcher(test_db):
            add_profile("p1")
            add_profile("p2")
            add_profile("p3")
            update_profile_enabled("p2", False)
            active = get_active_profile_ids()
            assert "p1" in active
            assert "p3" in active
            assert "p2" not in active

    def test_get_active_profile_ids_falls_back_to_env(self, test_db, monkeypatch):
        """Falls back to PROFILE_IDS env var when DB table is empty."""
        from models import get_active_profile_ids

        monkeypatch.setenv("PROFILE_IDS", "env1,env2")
        with _make_session_patcher(test_db):
            ids = get_active_profile_ids()
            assert ids == ["env1", "env2"]

    def test_update_profile_enabled(self, test_db):
        """update_profile_enabled toggles enabled status."""
        from models import add_profile, update_profile_enabled, get_profile

        with _make_session_patcher(test_db):
            add_profile("p1")
            assert update_profile_enabled("p1", False) is True
            assert get_profile("p1").enabled is False
            assert update_profile_enabled("p1", True) is True
            assert get_profile("p1").enabled is True

    def test_update_nonexistent_profile_returns_false(self, test_db):
        """update_profile_enabled returns False for unknown profile_id."""
        from models import update_profile_enabled

        with _make_session_patcher(test_db):
            assert update_profile_enabled("nope", True) is False

    def test_get_all_profiles_returns_all(self, test_db):
        """get_all_profiles returns both enabled and disabled profiles."""
        from models import add_profile, update_profile_enabled, get_all_profiles

        with _make_session_patcher(test_db):
            add_profile("p1")
            add_profile("p2")
            update_profile_enabled("p2", False)
            rows = get_all_profiles()
            ids = [r.profile_id for r in rows]
            assert "p1" in ids
            assert "p2" in ids


class TestDeleteProfileData:
    """Test data cleanup on profile deletion."""

    def test_delete_profile_data_removes_logs_and_status(self, test_db):
        """delete_profile_data removes DNS logs and fetch status for a profile."""
        from models import delete_profile_data
        from datetime import datetime, timezone

        # Insert DNS logs for two profiles
        for i in range(5):
            test_db.add(
                DNSLog(
                    timestamp=datetime.now(timezone.utc),
                    domain=f"test{i}.com",
                    profile_id="victim",
                    client_ip=f"1.1.1.{i}",
                    data="{}",
                )
            )
        for i in range(3):
            test_db.add(
                DNSLog(
                    timestamp=datetime.now(timezone.utc),
                    domain=f"keep{i}.com",
                    profile_id="keeper",
                    client_ip=f"2.2.2.{i}",
                    data="{}",
                )
            )
        test_db.add(
            FetchStatus(
                profile_id="victim",
                last_fetch_timestamp=datetime.now(timezone.utc),
                records_fetched=5,
            )
        )
        test_db.commit()

        with _make_session_patcher(test_db):
            result = delete_profile_data("victim")

        assert result["dns_logs_deleted"] == 5
        assert result["fetch_status_deleted"] == 1
        # Keeper logs must be untouched
        remaining = test_db.query(DNSLog).filter_by(profile_id="keeper").count()
        assert remaining == 3

    def test_delete_profile_removes_profile_row(self, test_db):
        """delete_profile removes the NextDNSProfile row and its data."""
        from models import add_profile, delete_profile

        with _make_session_patcher(test_db):
            add_profile("victim")
            result = delete_profile("victim", delete_data=False)
            assert result["deleted"] is True
            row = test_db.query(NextDNSProfile).filter_by(profile_id="victim").first()
            assert row is None

    def test_delete_nonexistent_profile_returns_deleted_false(self, test_db):
        """delete_profile returns deleted=False for unknown profile."""
        from models import delete_profile

        with _make_session_patcher(test_db):
            result = delete_profile("ghost")
            assert result["deleted"] is False


class TestMigrateConfigFromEnv:
    """Test one-time startup migration from env vars."""

    def test_seeds_api_key_and_profiles_when_empty(self, test_db, monkeypatch):
        """migrate_config_from_env seeds DB from env vars on first boot."""
        from models import (
            migrate_config_from_env,
            get_setting,
            get_active_profile_ids,
        )

        monkeypatch.setenv("API_KEY", "migrate-key")
        monkeypatch.setenv("PROFILE_IDS", "p1,p2")

        with _make_session_patcher(test_db):
            seeded = migrate_config_from_env()
            assert seeded is True
            assert get_setting("nextdns_api_key") == "migrate-key"
            ids = get_active_profile_ids()
            assert "p1" in ids
            assert "p2" in ids

    def test_skips_migration_when_tables_populated(self, test_db, monkeypatch):
        """migrate_config_from_env is a no-op when tables already have data."""
        from models import migrate_config_from_env, set_nextdns_api_key, add_profile

        monkeypatch.setenv("API_KEY", "new-key")
        monkeypatch.setenv("PROFILE_IDS", "new-profile")

        with _make_session_patcher(test_db):
            set_nextdns_api_key("existing-key")
            add_profile("existing-profile")
            seeded = migrate_config_from_env()
            assert seeded is False
            # Original values must not be overwritten
            row = test_db.query(SystemSetting).filter_by(key="nextdns_api_key").first()
            assert row.value == "existing-key"

    def test_migration_without_env_vars(self, test_db, monkeypatch):
        """migrate_config_from_env handles missing env vars gracefully."""
        from models import migrate_config_from_env

        monkeypatch.delenv("API_KEY", raising=False)
        monkeypatch.delenv("PROFILE_IDS", raising=False)
        monkeypatch.delenv("FETCH_INTERVAL", raising=False)
        monkeypatch.delenv("FETCH_LIMIT", raising=False)
        monkeypatch.delenv("LOG_LEVEL", raising=False)

        with _make_session_patcher(test_db):
            seeded = migrate_config_from_env()
            # Returns False because nothing was actually seeded
            assert seeded is False


class TestMaskApiKey:
    """Test the API key masking utility in main.py."""

    def test_mask_long_key(self):
        """Last 4 chars are visible, rest are bullets."""
        from main import _mask_api_key

        assert _mask_api_key("abcdef1234") == "••••••1234"

    def test_mask_short_key(self):
        """Keys of 4 chars or less are fully masked."""
        from main import _mask_api_key

        assert _mask_api_key("ab") == "••••"
        assert _mask_api_key("abcd") == "••••"

    def test_mask_exact_five_chars(self):
        """5-char key shows last 4."""
        from main import _mask_api_key

        assert _mask_api_key("abcde") == "•bcde"
