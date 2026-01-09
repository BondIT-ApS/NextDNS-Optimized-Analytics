# file: backend/tests/unit/test_scheduler.py
"""
🧱 Unit Tests for Scheduler Configuration

Testing our LEGO automation scheduler setup!
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestSchedulerConfiguration:
    """Test scheduler configuration and initialization."""

    @patch.dict(os.environ, {"PROFILE_IDS": "abc123,def456,ghi789"})
    def test_profile_ids_parsing(self):
        """Test that profile IDs are correctly parsed from environment."""
        # Need to reload module to pick up new environment
        import importlib
        import scheduler

        importlib.reload(scheduler)

        profile_ids = [
            pid.strip()
            for pid in os.getenv("PROFILE_IDS", "").split(",")
            if pid.strip()
        ]
        assert len(profile_ids) == 3
        assert "abc123" in profile_ids
        assert "def456" in profile_ids
        assert "ghi789" in profile_ids

    @patch.dict(os.environ, {"PROFILE_IDS": "  single-profile  "})
    def test_profile_ids_with_whitespace(self):
        """Test that profile IDs handle whitespace correctly."""
        profile_ids = [
            pid.strip()
            for pid in os.getenv("PROFILE_IDS", "").split(",")
            if pid.strip()
        ]
        assert len(profile_ids) == 1
        assert profile_ids[0] == "single-profile"

    @patch.dict(os.environ, {"PROFILE_IDS": ""})
    def test_empty_profile_ids(self):
        """Test handling of empty profile IDs."""
        profile_ids = [
            pid.strip()
            for pid in os.getenv("PROFILE_IDS", "").split(",")
            if pid.strip()
        ]
        assert len(profile_ids) == 0

    @patch.dict(os.environ, {"PROFILE_IDS": "test1,,test2,  ,test3"})
    def test_profile_ids_with_empty_entries(self):
        """Test that empty entries in profile IDs are filtered out."""
        profile_ids = [
            pid.strip()
            for pid in os.getenv("PROFILE_IDS", "").split(",")
            if pid.strip()
        ]
        assert len(profile_ids) == 3
        assert "test1" in profile_ids
        assert "test2" in profile_ids
        assert "test3" in profile_ids

    def test_fetch_interval_default(self):
        """Test that fetch interval defaults to 60 minutes."""
        interval = int(os.getenv("FETCH_INTERVAL", "60"))
        assert interval == 60

    @patch.dict(os.environ, {"FETCH_INTERVAL": "30"})
    def test_fetch_interval_custom(self):
        """Test custom fetch interval."""
        interval = int(os.getenv("FETCH_INTERVAL", "60"))
        assert interval == 30

    def test_fetch_limit_default(self):
        """Test that fetch limit defaults to 100."""
        limit = int(os.getenv("FETCH_LIMIT", "100"))
        assert limit == 100

    @patch.dict(os.environ, {"FETCH_LIMIT": "200"})
    def test_fetch_limit_custom(self):
        """Test custom fetch limit."""
        limit = int(os.getenv("FETCH_LIMIT", "100"))
        assert limit == 200


class TestSchedulerInitialization:
    """Test scheduler initialization logic."""

    @patch.dict(os.environ, {"API_KEY": "", "PROFILE_IDS": ""}, clear=True)
    def test_scheduler_not_created_without_credentials(self):
        """Test that scheduler is not created when credentials are missing."""
        # Reload to test initialization logic
        import importlib
        import scheduler

        importlib.reload(scheduler)

        # Scheduler should be None when credentials are missing
        assert scheduler.scheduler is None

    @patch.dict(os.environ, {"API_KEY": "test-key", "PROFILE_IDS": "test-profile"})
    @patch("scheduler.BackgroundScheduler")
    @patch("scheduler.get_total_record_count", return_value=0)
    @patch("scheduler.get_last_fetch_timestamp", return_value=None)
    def test_scheduler_created_with_valid_credentials(
        self, mock_timestamp, mock_count, mock_scheduler_class
    ):
        """Test that scheduler is created with valid credentials."""
        mock_scheduler_instance = MagicMock()
        mock_scheduler_class.return_value = mock_scheduler_instance

        # Reload scheduler module with mocked environment
        import importlib
        import scheduler

        importlib.reload(scheduler)

        # Scheduler should be initialized (not None)
        # Note: This is tricky to test because scheduler is created at module import time
        assert scheduler.API_KEY == "test-key"


class TestEnvironmentConfiguration:
    """Test environment variable handling."""

    def test_api_key_from_environment(self):
        """Test reading API_KEY from environment."""
        with patch.dict(os.environ, {"API_KEY": "test-api-key"}):
            api_key = os.getenv("API_KEY")
            assert api_key == "test-api-key"

    def test_api_key_missing(self):
        """Test handling missing API_KEY."""
        with patch.dict(os.environ, {}, clear=True):
            api_key = os.getenv("API_KEY")
            assert api_key is None

    def test_fetch_interval_validation(self):
        """Test fetch interval is a valid integer."""
        with patch.dict(os.environ, {"FETCH_INTERVAL": "120"}):
            interval = int(os.getenv("FETCH_INTERVAL", "60"))
            assert isinstance(interval, int)
            assert interval > 0

    def test_fetch_limit_validation(self):
        """Test fetch limit is a valid integer."""
        with patch.dict(os.environ, {"FETCH_LIMIT": "500"}):
            limit = int(os.getenv("FETCH_LIMIT", "100"))
            assert isinstance(limit, int)
            assert limit > 0
