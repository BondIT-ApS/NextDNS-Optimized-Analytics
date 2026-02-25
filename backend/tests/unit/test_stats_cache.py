# file: backend/tests/unit/test_stats_cache.py
"""
🧱 Unit Tests for Stats Cache Module (issue #183)

Tests the two-level caching system: TTL in-memory cache (L1) and the
pre-computed stats_cache DB table (L2). All DB calls are mocked so no
real database connection is required.

Coverage targets:
  - make_cache_key: key format, sorting, None profile, extra kwargs
  - get_cached:     L1 hit, L2 hit + L1 warm, invalid JSON, full miss
  - store_cached:   L1 write, DB upsert, serialization error, overwrite
  - invalidate_memory_cache: clear all, clear by profile, no-op on miss
  - precompute_all_stats: full run, empty profiles, per-stat error isolation,
                           granularity mapping, group_by, exclusion defaults
"""

import json
from unittest.mock import patch

import pytest

import stats_cache
from stats_cache import (
    _GRANULARITY_MAP,
    PRECOMPUTE_RANGES,
    get_cached,
    invalidate_memory_cache,
    make_cache_key,
    precompute_all_stats,
    store_cached,
)

pytestmark = pytest.mark.unit

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

# Minimal valid return values for each stat function
_OVERVIEW = {
    "total_queries": 100,
    "blocked_queries": 10,
    "allowed_queries": 90,
    "blocked_percentage": 10.0,
    "queries_per_hour": 4.2,
    "most_active_device": None,
    "top_blocked_domain": None,
}
_TIMESERIES = [
    {
        "timestamp": "2026-01-01T00:00:00",
        "total_queries": 5,
        "blocked_queries": 1,
        "allowed_queries": 4,
    }
]
_DOMAINS = {"blocked_domains": [], "allowed_domains": []}
_TLDS = {"blocked_tlds": [], "allowed_tlds": []}
_DEVICES = [
    {
        "device_name": "MacBook",
        "total_queries": 50,
        "blocked_queries": 5,
        "allowed_queries": 45,
        "blocked_percentage": 10.0,
        "allowed_percentage": 90.0,
        "last_activity": "2026-01-01T00:00:00",
    }
]


@pytest.fixture(autouse=True)
def clear_memory_cache():
    """Reset the in-memory TTL cache before and after every test."""
    stats_cache._MEMORY_CACHE.clear()
    yield
    stats_cache._MEMORY_CACHE.clear()


@pytest.fixture
def mock_stat_functions(request):
    """Patch all five stat model functions + upsert + active profiles.

    Pass active_profiles=[...] via indirect or use the default ["p1"].
    """
    active_profiles = getattr(request, "param", ["p1"])
    with (
        patch(
            "stats_cache.get_active_profile_ids", return_value=active_profiles
        ) as m_profiles,
        patch("stats_cache.get_stats_overview", return_value=_OVERVIEW) as m_ov,
        patch("stats_cache.get_stats_timeseries", return_value=_TIMESERIES) as m_ts,
        patch("stats_cache.get_top_domains", return_value=_DOMAINS) as m_dom,
        patch("stats_cache.get_stats_tlds", return_value=_TLDS) as m_tld,
        patch("stats_cache.get_stats_devices", return_value=_DEVICES) as m_dev,
        patch("stats_cache.upsert_db_stats_cache", return_value=True) as m_upsert,
    ):
        yield {
            "profiles": m_profiles,
            "overview": m_ov,
            "timeseries": m_ts,
            "domains": m_dom,
            "tlds": m_tld,
            "devices": m_dev,
            "upsert": m_upsert,
        }


# ---------------------------------------------------------------------------
# make_cache_key
# ---------------------------------------------------------------------------


class TestMakeCacheKey:
    """make_cache_key builds deterministic, human-readable cache keys."""

    def test_basic_key_no_kwargs(self):
        """Base key format: stat_type:profile_all:range_<range>."""
        key = make_cache_key("overview", None, "24h")
        assert key == "overview:profile_all:range_24h"

    def test_specific_profile_included(self):
        """Named profile appears in the key."""
        key = make_cache_key("overview", "abc123", "24h")
        assert key == "overview:profile_abc123:range_24h"

    def test_none_profile_maps_to_all(self):
        """None profile maps to the 'all' sentinel."""
        key = make_cache_key("domains", None, "7d")
        assert "profile_all" in key

    def test_kwargs_appended_to_base(self):
        """Additional kwargs are appended after the base key."""
        key = make_cache_key("timeseries", None, "24h", gran="hour", group="status")
        assert key.startswith("timeseries:profile_all:range_24h:")
        assert "gran_hour" in key
        assert "group_status" in key

    def test_kwargs_sorted_for_determinism(self):
        """Key is the same regardless of kwargs insertion order."""
        key1 = make_cache_key("timeseries", None, "24h", gran="hour", group="status")
        key2 = make_cache_key("timeseries", None, "24h", group="status", gran="hour")
        assert key1 == key2

    def test_limit_kwarg_included(self):
        """Limit kwarg is correctly formatted."""
        key = make_cache_key("domains", "p1", "7d", limit=10)
        assert key == "domains:profile_p1:range_7d:limit_10"

    def test_different_stat_types_produce_unique_keys(self):
        """All five stat type prefixes produce distinct keys."""
        stat_types = ["overview", "timeseries", "domains", "tlds", "devices"]
        keys = [make_cache_key(t, None, "24h") for t in stat_types]
        assert len(set(keys)) == len(stat_types)

    def test_different_time_ranges_produce_unique_keys(self):
        """Each precompute range yields a different key."""
        keys = [make_cache_key("overview", None, r) for r in PRECOMPUTE_RANGES]
        assert len(set(keys)) == len(PRECOMPUTE_RANGES)

    def test_different_profiles_produce_unique_keys(self):
        """Keys for different profile IDs are distinct."""
        key_all = make_cache_key("overview", None, "24h")
        key_p1 = make_cache_key("overview", "p1", "24h")
        key_p2 = make_cache_key("overview", "p2", "24h")
        assert key_all != key_p1 != key_p2

    def test_no_extra_separators_without_kwargs(self):
        """Base key has no trailing colon when no kwargs are passed."""
        key = make_cache_key("overview", None, "24h")
        assert not key.endswith(":")

    def test_timeseries_key_with_all_params(self):
        """Full timeseries key encodes granularity and group_by."""
        key = make_cache_key("timeseries", "p1", "7d", gran="day", group="status")
        assert key == "timeseries:profile_p1:range_7d:gran_day:group_status"


# ---------------------------------------------------------------------------
# get_cached
# ---------------------------------------------------------------------------


class TestGetCached:
    """get_cached checks L1 (memory) then L2 (DB) and returns None on full miss."""

    def test_l1_hit_returns_value_without_db(self):
        """In-memory hit is returned immediately; DB is not queried."""
        stats_cache._MEMORY_CACHE["test:key"] = {"total": 42}

        with patch("stats_cache.get_db_stats_cache") as mock_db:
            result = get_cached("test:key")

        assert result == {"total": 42}
        mock_db.assert_not_called()

    def test_l2_hit_deserializes_payload(self):
        """DB cache hit returns deserialized Python object."""
        payload = {"total_queries": 100, "blocked_queries": 10}
        with patch("stats_cache.get_db_stats_cache", return_value=json.dumps(payload)):
            result = get_cached("db:key")

        assert result == payload

    def test_l2_hit_warms_l1_cache(self):
        """DB hit populates in-memory cache so next call skips the DB."""
        payload = {"val": 99}
        with patch("stats_cache.get_db_stats_cache", return_value=json.dumps(payload)):
            get_cached("warm:key")

        assert "warm:key" in stats_cache._MEMORY_CACHE

    def test_l2_hit_subsequent_call_is_l1(self):
        """After L2 warms L1, the second request does not hit the DB."""
        payload = {"val": 1}
        with patch("stats_cache.get_db_stats_cache", return_value=json.dumps(payload)):
            get_cached("warm2:key")

        with patch("stats_cache.get_db_stats_cache") as mock_db:
            result = get_cached("warm2:key")

        assert result == payload
        mock_db.assert_not_called()

    def test_l2_invalid_json_returns_none(self):
        """Corrupted JSON in the DB cache returns None without raising."""
        with patch("stats_cache.get_db_stats_cache", return_value="not-valid-json{{"):
            result = get_cached("bad:key")

        assert result is None

    def test_l2_invalid_json_does_not_warm_l1(self):
        """Invalid DB payload must not be stored in the memory cache."""
        with patch("stats_cache.get_db_stats_cache", return_value="bad json"):
            get_cached("corrupt:key")

        assert "corrupt:key" not in stats_cache._MEMORY_CACHE

    def test_full_miss_returns_none(self):
        """Both caches empty → None."""
        with patch("stats_cache.get_db_stats_cache", return_value=None):
            result = get_cached("missing:key")

        assert result is None

    def test_l2_empty_string_is_treated_as_miss(self):
        """Empty string from DB is falsy and treated as a cache miss."""
        with patch("stats_cache.get_db_stats_cache", return_value=""):
            result = get_cached("empty:key")

        assert result is None

    def test_l2_hit_with_list_payload(self):
        """List values (e.g. timeseries) are correctly round-tripped."""
        payload = [{"timestamp": "2026-01-01", "total_queries": 5}]
        with patch("stats_cache.get_db_stats_cache", return_value=json.dumps(payload)):
            result = get_cached("list:key")

        assert result == payload


# ---------------------------------------------------------------------------
# store_cached
# ---------------------------------------------------------------------------


class TestStoreCached:
    """store_cached writes to both L1 (memory) and L2 (DB)."""

    def test_stores_in_memory_cache(self):
        """Value is accessible from _MEMORY_CACHE immediately after store."""
        with patch("stats_cache.upsert_db_stats_cache"):
            store_cached("store:key", {"data": "value"})

        assert stats_cache._MEMORY_CACHE["store:key"] == {"data": "value"}

    def test_calls_upsert_with_correct_args(self):
        """DB upsert receives the cache key and a valid JSON string."""
        value = {"total": 5, "blocked": 2}
        with patch("stats_cache.upsert_db_stats_cache") as mock_upsert:
            store_cached("upsert:key", value)

        mock_upsert.assert_called_once()
        key_arg, payload_arg = mock_upsert.call_args[0]
        assert key_arg == "upsert:key"
        assert json.loads(payload_arg) == value

    def test_l1_readable_via_get_cached_after_store(self):
        """Stored value is immediately retrievable through get_cached (L1)."""
        with patch("stats_cache.upsert_db_stats_cache"):
            store_cached("read:key", [1, 2, 3])

        with patch("stats_cache.get_db_stats_cache") as mock_db:
            result = get_cached("read:key")

        assert result == [1, 2, 3]
        mock_db.assert_not_called()

    def test_stores_list_value(self):
        """List values (timeseries) are stored without coercion."""
        ts = [{"timestamp": "2026-01-01T00:00:00", "total": 10}]
        with patch("stats_cache.upsert_db_stats_cache"):
            store_cached("ts:key", ts)

        assert stats_cache._MEMORY_CACHE["ts:key"] == ts

    def test_overwrites_existing_entry(self):
        """Storing to an existing key replaces the old value."""
        with patch("stats_cache.upsert_db_stats_cache"):
            store_cached("ow:key", {"v": 1})
            store_cached("ow:key", {"v": 2})

        assert stats_cache._MEMORY_CACHE["ow:key"] == {"v": 2}

    def test_serialization_error_does_not_raise(self):
        """If json.dumps raises, store_cached logs the error but does not propagate."""
        with patch("stats_cache.json.dumps", side_effect=TypeError("cannot serialize")):
            with patch("stats_cache.upsert_db_stats_cache") as mock_upsert:
                store_cached("err:key", {"ok": True})  # must not raise

        # upsert should not have been called since serialization failed
        mock_upsert.assert_not_called()

    def test_l1_still_set_even_when_db_upsert_skipped(self):
        """L1 is written before the try/except, so it's set even if serialization fails."""
        with patch("stats_cache.json.dumps", side_effect=TypeError("bad")):
            with patch("stats_cache.upsert_db_stats_cache"):
                store_cached("l1only:key", {"x": 1})

        assert "l1only:key" in stats_cache._MEMORY_CACHE

    def test_nested_structure_stored_correctly(self):
        """Complex nested dicts/lists are JSON round-tripped without loss."""
        value = {
            "blocked_domains": [{"domain": "evil.com", "count": 10, "percentage": 5.0}],
            "allowed_domains": [],
        }
        with patch("stats_cache.upsert_db_stats_cache") as mock_upsert:
            store_cached("nested:key", value)

        _, payload = mock_upsert.call_args[0]
        assert json.loads(payload) == value


# ---------------------------------------------------------------------------
# invalidate_memory_cache
# ---------------------------------------------------------------------------


class TestInvalidateMemoryCache:
    """invalidate_memory_cache clears L1 entries globally or by profile."""

    def test_clear_all_empties_cache(self):
        """Called with no argument, clears every entry."""
        stats_cache._MEMORY_CACHE["key1"] = 1
        stats_cache._MEMORY_CACHE["key2"] = 2

        invalidate_memory_cache()

        assert len(stats_cache._MEMORY_CACHE) == 0

    def test_clear_by_profile_removes_matching_keys(self):
        """Only keys whose string contains 'profile_<id>' are removed."""
        stats_cache._MEMORY_CACHE["overview:profile_abc:range_24h"] = 1
        stats_cache._MEMORY_CACHE["domains:profile_abc:range_7d"] = 2
        stats_cache._MEMORY_CACHE["overview:profile_xyz:range_24h"] = 3

        invalidate_memory_cache(profile_id="abc")

        assert "overview:profile_abc:range_24h" not in stats_cache._MEMORY_CACHE
        assert "domains:profile_abc:range_7d" not in stats_cache._MEMORY_CACHE
        # Unrelated profile must be untouched
        assert "overview:profile_xyz:range_24h" in stats_cache._MEMORY_CACHE

    def test_clear_by_nonexistent_profile_is_noop(self):
        """No entries match → cache unchanged, no error."""
        stats_cache._MEMORY_CACHE["overview:profile_other:range_24h"] = 1

        invalidate_memory_cache(profile_id="ghost")

        assert "overview:profile_other:range_24h" in stats_cache._MEMORY_CACHE

    def test_clear_all_on_empty_cache_is_safe(self):
        """Clearing an already-empty cache does not raise."""
        invalidate_memory_cache()  # should not raise

    def test_clear_by_profile_on_empty_cache_is_safe(self):
        """Clearing by profile on empty cache does not raise."""
        invalidate_memory_cache(profile_id="nobody")  # should not raise

    def test_clear_all_profile_view(self):
        """The 'all profiles' key (profile_all) can be targeted by profile_id='all'."""
        stats_cache._MEMORY_CACHE["overview:profile_all:range_24h"] = 1
        stats_cache._MEMORY_CACHE["overview:profile_abc:range_24h"] = 2

        invalidate_memory_cache(profile_id="all")

        assert "overview:profile_all:range_24h" not in stats_cache._MEMORY_CACHE
        assert "overview:profile_abc:range_24h" in stats_cache._MEMORY_CACHE

    def test_multiple_profiles_only_target_cleared(self):
        """With entries for multiple profiles, only the specified one is evicted."""
        profiles = ["a", "b", "c"]
        for p in profiles:
            stats_cache._MEMORY_CACHE[f"overview:profile_{p}:range_24h"] = 1

        invalidate_memory_cache(profile_id="b")

        assert "overview:profile_a:range_24h" in stats_cache._MEMORY_CACHE
        assert "overview:profile_b:range_24h" not in stats_cache._MEMORY_CACHE
        assert "overview:profile_c:range_24h" in stats_cache._MEMORY_CACHE


# ---------------------------------------------------------------------------
# precompute_all_stats
# ---------------------------------------------------------------------------


class TestPrecomputeAllStats:
    """precompute_all_stats iterates profiles × ranges × stat types."""

    def test_calls_all_five_stat_functions(self, mock_stat_functions):
        """Each of the 5 stat types is computed for every profile/range combo."""
        precompute_all_stats()

        # 2 profiles (None + "p1") × 5 ranges
        expected = 2 * len(PRECOMPUTE_RANGES)
        assert mock_stat_functions["overview"].call_count == expected
        assert mock_stat_functions["timeseries"].call_count == expected
        assert mock_stat_functions["domains"].call_count == expected
        assert mock_stat_functions["tlds"].call_count == expected
        assert mock_stat_functions["devices"].call_count == expected

    def test_always_includes_none_profile(self, mock_stat_functions):
        """None profile (all-profiles combined view) is always computed."""
        precompute_all_stats()
        profile_args = [
            c.kwargs.get("profile_filter")
            for c in mock_stat_functions["overview"].call_args_list
        ]
        assert None in profile_args

    def test_includes_each_active_profile(self, mock_stat_functions):
        """Active profiles from get_active_profile_ids are computed."""
        precompute_all_stats()
        profile_args = [
            c.kwargs.get("profile_filter")
            for c in mock_stat_functions["overview"].call_args_list
        ]
        assert "p1" in profile_args

    def test_covers_all_precompute_ranges(self, mock_stat_functions):
        """Every range in PRECOMPUTE_RANGES is computed."""
        precompute_all_stats()
        time_ranges = {
            c.kwargs.get("time_range")
            for c in mock_stat_functions["overview"].call_args_list
        }
        assert time_ranges == set(PRECOMPUTE_RANGES)

    def test_results_stored_in_memory_cache(self, mock_stat_functions):
        """Computed values land in _MEMORY_CACHE under the correct key."""
        precompute_all_stats()
        key = make_cache_key("overview", None, "24h")
        assert stats_cache._MEMORY_CACHE[key] == _OVERVIEW

    def test_results_stored_in_db_cache(self, mock_stat_functions):
        """upsert_db_stats_cache is called once per computed entry."""
        precompute_all_stats()
        # 2 profiles × 5 ranges × 5 stat types = 50
        expected = 2 * len(PRECOMPUTE_RANGES) * 5
        assert mock_stat_functions["upsert"].call_count == expected

    def test_empty_active_profiles_computes_only_all_view(self):
        """When there are no configured profiles, only None profile is computed."""
        with (
            patch("stats_cache.get_active_profile_ids", return_value=[]),
            patch("stats_cache.get_stats_overview", return_value=_OVERVIEW) as m_ov,
            patch("stats_cache.get_stats_timeseries", return_value=_TIMESERIES),
            patch("stats_cache.get_top_domains", return_value=_DOMAINS),
            patch("stats_cache.get_stats_tlds", return_value=_TLDS),
            patch("stats_cache.get_stats_devices", return_value=_DEVICES),
            patch("stats_cache.upsert_db_stats_cache"),
        ):
            precompute_all_stats()

        # Only 1 profile (None) × 5 ranges
        assert m_ov.call_count == len(PRECOMPUTE_RANGES)

    def test_multiple_active_profiles_all_computed(self):
        """All active profiles appear in the computed set."""
        with (
            patch(
                "stats_cache.get_active_profile_ids", return_value=["p1", "p2", "p3"]
            ),
            patch("stats_cache.get_stats_overview", return_value=_OVERVIEW) as m_ov,
            patch("stats_cache.get_stats_timeseries", return_value=_TIMESERIES),
            patch("stats_cache.get_top_domains", return_value=_DOMAINS),
            patch("stats_cache.get_stats_tlds", return_value=_TLDS),
            patch("stats_cache.get_stats_devices", return_value=_DEVICES),
            patch("stats_cache.upsert_db_stats_cache"),
        ):
            precompute_all_stats()

        # 4 profiles (None + p1 + p2 + p3) × 5 ranges
        assert m_ov.call_count == 4 * len(PRECOMPUTE_RANGES)

    def test_overview_error_does_not_abort_other_stat_types(self, mock_stat_functions):
        """A failing overview computation is isolated; other types still run."""
        mock_stat_functions["overview"].side_effect = Exception("DB timeout")

        precompute_all_stats()  # must not raise

        # Timeseries and others should have run fully
        assert mock_stat_functions["timeseries"].call_count == 2 * len(
            PRECOMPUTE_RANGES
        )
        assert mock_stat_functions["domains"].call_count == 2 * len(PRECOMPUTE_RANGES)

    def test_timeseries_error_does_not_abort_other_stat_types(
        self, mock_stat_functions
    ):
        """Timeseries failure is isolated."""
        mock_stat_functions["timeseries"].side_effect = RuntimeError("timeout")

        precompute_all_stats()

        assert mock_stat_functions["overview"].call_count == 2 * len(PRECOMPUTE_RANGES)
        assert mock_stat_functions["domains"].call_count == 2 * len(PRECOMPUTE_RANGES)

    def test_domains_error_does_not_abort_tlds_or_devices(self, mock_stat_functions):
        """Domains failure is isolated; tlds and devices still run."""
        mock_stat_functions["domains"].side_effect = Exception("query error")

        precompute_all_stats()

        assert mock_stat_functions["tlds"].call_count == 2 * len(PRECOMPUTE_RANGES)
        assert mock_stat_functions["devices"].call_count == 2 * len(PRECOMPUTE_RANGES)

    def test_all_stats_fail_does_not_raise(self, mock_stat_functions):
        """Total failure across all stat types must not propagate to the caller."""
        for key in ["overview", "timeseries", "domains", "tlds", "devices"]:
            mock_stat_functions[key].side_effect = Exception("total failure")

        precompute_all_stats()  # must not raise

    def test_timeseries_uses_correct_granularity(self, mock_stat_functions):
        """Each time range is paired with its auto-granularity from _GRANULARITY_MAP."""
        precompute_all_stats()
        for c in mock_stat_functions["timeseries"].call_args_list:
            time_range = c.kwargs.get("time_range")
            granularity = c.kwargs.get("granularity")
            expected = _GRANULARITY_MAP.get(time_range, "hour")
            assert granularity == expected, (
                f"Wrong granularity for {time_range}: "
                f"expected {expected}, got {granularity}"
            )

    def test_timeseries_always_uses_status_group_by(self, mock_stat_functions):
        """Timeseries pre-computation always uses group_by='status'."""
        precompute_all_stats()
        for c in mock_stat_functions["timeseries"].call_args_list:
            assert c.kwargs.get("group_by") == "status"

    def test_devices_called_without_any_exclusions(self, mock_stat_functions):
        """Device stats are precomputed with no device or domain exclusions."""
        precompute_all_stats()
        for c in mock_stat_functions["devices"].call_args_list:
            assert c.kwargs.get("exclude_devices") is None
            assert c.kwargs.get("exclude_domains") is None

    def test_domains_called_without_domain_exclusions(self, mock_stat_functions):
        """Domain stats are precomputed with no domain exclusions."""
        precompute_all_stats()
        for c in mock_stat_functions["domains"].call_args_list:
            assert c.kwargs.get("exclude_domains") is None

    def test_tlds_called_without_domain_exclusions(self, mock_stat_functions):
        """TLD stats are precomputed with no domain exclusions."""
        precompute_all_stats()
        for c in mock_stat_functions["tlds"].call_args_list:
            assert c.kwargs.get("exclude_domains") is None

    def test_all_stat_types_stored_in_memory(self, mock_stat_functions):
        """After precompute, all five stat types for all profiles are in L1."""
        precompute_all_stats()

        for time_range in PRECOMPUTE_RANGES:
            for profile in [None, "p1"]:
                gran = _GRANULARITY_MAP.get(time_range, "hour")
                assert (
                    make_cache_key("overview", profile, time_range)
                    in stats_cache._MEMORY_CACHE
                )
                assert (
                    make_cache_key(
                        "timeseries", profile, time_range, gran=gran, group="status"
                    )
                    in stats_cache._MEMORY_CACHE
                )
                assert (
                    make_cache_key("domains", profile, time_range, limit=10)
                    in stats_cache._MEMORY_CACHE
                )
                assert (
                    make_cache_key("tlds", profile, time_range, limit=10)
                    in stats_cache._MEMORY_CACHE
                )
                assert (
                    make_cache_key("devices", profile, time_range, limit=10)
                    in stats_cache._MEMORY_CACHE
                )

    def test_overview_called_with_no_exclude_domains(self, mock_stat_functions):
        """Overview is always computed without domain exclusions."""
        precompute_all_stats()
        for c in mock_stat_functions["overview"].call_args_list:
            assert c.kwargs.get("exclude_domains") is None
