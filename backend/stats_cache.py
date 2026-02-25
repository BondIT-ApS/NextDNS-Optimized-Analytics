# file: backend/stats_cache.py
"""🧱 Stats Cache — two-level caching for dashboard statistics (issue #183).

Architecture
------------
Level 1 — cachetools.TTLCache (in-memory, 5-minute TTL, per-process)
  Fast path: avoids DB round-trips for frequently requested stats.
  Entries expire after 5 minutes; the next request triggers a DB lookup
  or live computation.

Level 2 — stats_cache DB table (persistent, updated by scheduler)
  Warm path: if the memory cache has expired, the DB cache serves the
  last precomputed result without running aggregation queries on dns_logs.
  The scheduler calls precompute_all_stats() after each fetch cycle, so
  DB cache entries are refreshed roughly every FETCH_INTERVAL minutes.

Fallback — live query
  If both caches miss (e.g. first boot before the scheduler has run), the
  endpoint falls through to the normal database aggregation.

Cache keys
----------
Keys encode all parameters that affect the result:
  "overview:profile_all:range_24h"
  "timeseries:profile_abc123:range_7d:gran_day:group_status"
  "domains:profile_all:range_24h:limit_10"

Only "default" requests (no custom exclude/wildcard domain filters) are
cached; requests with custom filters always run live.
"""

import json
from typing import Any, Optional

from cachetools import TTLCache

from models import (
    get_active_profile_ids,
    get_db_stats_cache,
    get_stats_devices,
    get_stats_overview,
    get_stats_timeseries,
    get_stats_tlds,
    get_top_domains,
    upsert_db_stats_cache,
)
from logging_config import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Level 1 — in-memory TTL cache
# ---------------------------------------------------------------------------

# maxsize: max entries (~1–10 KB JSON each); 512 covers all profiles × ranges
# ttl: seconds before an entry is evicted
_MEMORY_CACHE: TTLCache = TTLCache(maxsize=512, ttl=300)  # 5-minute TTL

# Time ranges to precompute after each scheduler fetch cycle.
# "30m" and "3m"/"all" are omitted: short-range data changes too fast for
# meaningful pre-computation; long-range is expensive and infrequently viewed.
PRECOMPUTE_RANGES = ["1h", "6h", "24h", "7d", "30d"]

# Auto-granularity map (mirrors the logic in main.py)
_GRANULARITY_MAP = {
    "30m": "1min",
    "1h": "5min",
    "6h": "15min",
    "24h": "hour",
    "7d": "day",
    "30d": "day",
    "3m": "week",
    "all": "week",
}


# ---------------------------------------------------------------------------
# Cache key helpers
# ---------------------------------------------------------------------------


def make_cache_key(
    stat_type: str, profile: Optional[str], time_range: str, **kwargs
) -> str:
    """Build a deterministic cache key from stat parameters.

    Args:
        stat_type: One of "overview", "timeseries", "domains", "tlds", "devices".
        profile: Profile ID or None to represent "all profiles".
        time_range: Time range string (e.g. "24h", "7d").
        **kwargs: Additional differentiating params (gran, group, limit, …).

    Returns:
        Cache key string, e.g. "overview:profile_all:range_24h".
    """
    profile_part = f"profile_{profile or 'all'}"
    range_part = f"range_{time_range}"
    base = f"{stat_type}:{profile_part}:{range_part}"

    if kwargs:
        extras = ":".join(f"{k}_{v}" for k, v in sorted(kwargs.items()))
        return f"{base}:{extras}"
    return base


# ---------------------------------------------------------------------------
# Public cache API
# ---------------------------------------------------------------------------


def get_cached(cache_key: str) -> Optional[Any]:
    """Return a cached value, checking memory then DB.

    Args:
        cache_key: The cache key to look up.

    Returns:
        Deserialized Python object, or None on cache miss.
    """
    # Level 1: in-memory
    if cache_key in _MEMORY_CACHE:
        logger.debug("⚡ Cache L1 hit: %s", cache_key)
        return _MEMORY_CACHE[cache_key]

    # Level 2: DB cache
    payload_str = get_db_stats_cache(cache_key)
    if payload_str:
        try:
            value = json.loads(payload_str)
            # Warm the memory cache so subsequent requests skip the DB
            _MEMORY_CACHE[cache_key] = value
            logger.debug("🗄️  Cache L2 hit: %s", cache_key)
            return value
        except json.JSONDecodeError:
            logger.warning("⚠️  Invalid JSON in stats_cache for key: %s", cache_key)

    logger.debug("❌ Cache miss: %s", cache_key)
    return None


def store_cached(cache_key: str, value: Any) -> None:
    """Store a value in both the memory cache and the DB cache.

    Args:
        cache_key: Cache key string.
        value: JSON-serializable Python object.
    """
    # Level 1: in-memory
    _MEMORY_CACHE[cache_key] = value

    # Level 2: DB cache
    try:
        payload_str = json.dumps(value, default=str)
        upsert_db_stats_cache(cache_key, payload_str)
    except (TypeError, ValueError) as e:
        logger.error(
            "❌ Failed to serialize stats for DB cache key %s: %s", cache_key, e
        )


def invalidate_memory_cache(profile_id: Optional[str] = None) -> None:
    """Clear in-memory cache entries.

    Args:
        profile_id: If specified, clear only entries for this profile.
                    If None, clear all entries.
    """
    if profile_id is None:
        _MEMORY_CACHE.clear()
        logger.info("🗑️  In-memory stats cache cleared (all entries)")
    else:
        keys_to_remove = [
            k for k in list(_MEMORY_CACHE.keys()) if f"profile_{profile_id}" in k
        ]
        for k in keys_to_remove:
            del _MEMORY_CACHE[k]
        logger.info(
            "🗑️  In-memory stats cache cleared for profile '%s' (%d entries)",
            profile_id,
            len(keys_to_remove),
        )


# ---------------------------------------------------------------------------
# Pre-computation — called by scheduler after each fetch cycle
# ---------------------------------------------------------------------------


def precompute_all_stats() -> None:
    """Pre-compute statistics for all active profiles and standard time ranges.

    Iterates over:
        profiles: [None (all profiles)] + active profile IDs
        time_ranges: PRECOMPUTE_RANGES (1h, 6h, 24h, 7d, 30d)
        stat types: overview, timeseries, domains, tlds, devices

    Results are stored in both the in-memory TTL cache and the stats_cache
    DB table so they survive process restarts.

    Errors in individual stat types are caught and logged so that one
    failing computation does not abort the rest of the precomputation run.
    """
    active_profiles = get_active_profile_ids()
    # Include None to represent the "all profiles" combined view
    profiles_to_compute = [None] + list(active_profiles)

    total_computed = 0
    total_errors = 0

    logger.info(
        "🔄 Pre-computing stats cache for %d profile(s) × %d time ranges (%d stat types each)",
        len(profiles_to_compute),
        len(PRECOMPUTE_RANGES),
        5,
    )

    for profile in profiles_to_compute:
        for time_range in PRECOMPUTE_RANGES:

            # 1. Overview
            try:
                key = make_cache_key("overview", profile, time_range)
                value = get_stats_overview(
                    profile_filter=profile,
                    time_range=time_range,
                    exclude_domains=None,
                )
                store_cached(key, value)
                total_computed += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to precompute overview [%s/%s]: %s",
                    profile,
                    time_range,
                    e,
                )
                total_errors += 1

            # 2. Timeseries — status grouping only ("profile" grouping is rare and computed live)
            try:
                granularity = _GRANULARITY_MAP.get(time_range, "hour")
                key = make_cache_key(
                    "timeseries",
                    profile,
                    time_range,
                    gran=granularity,
                    group="status",
                )
                value = get_stats_timeseries(
                    profile_filter=profile,
                    time_range=time_range,
                    granularity=granularity,
                    group_by="status",
                )
                store_cached(key, value)
                total_computed += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to precompute timeseries [%s/%s]: %s",
                    profile,
                    time_range,
                    e,
                )
                total_errors += 1

            # 3. Domains (default limit=10)
            try:
                key = make_cache_key("domains", profile, time_range, limit=10)
                value = get_top_domains(
                    profile_filter=profile,
                    time_range=time_range,
                    limit=10,
                    exclude_domains=None,
                )
                store_cached(key, value)
                total_computed += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to precompute domains [%s/%s]: %s",
                    profile,
                    time_range,
                    e,
                )
                total_errors += 1

            # 4. TLDs (default limit=10)
            try:
                key = make_cache_key("tlds", profile, time_range, limit=10)
                value = get_stats_tlds(
                    profile_filter=profile,
                    time_range=time_range,
                    limit=10,
                    exclude_domains=None,
                )
                store_cached(key, value)
                total_computed += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to precompute tlds [%s/%s]: %s",
                    profile,
                    time_range,
                    e,
                )
                total_errors += 1

            # 5. Devices (default limit=10, no exclusions)
            try:
                key = make_cache_key("devices", profile, time_range, limit=10)
                value = get_stats_devices(
                    profile_filter=profile,
                    time_range=time_range,
                    limit=10,
                    exclude_devices=None,
                    exclude_domains=None,
                )
                store_cached(key, value)
                total_computed += 1
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error(
                    "❌ Failed to precompute devices [%s/%s]: %s",
                    profile,
                    time_range,
                    e,
                )
                total_errors += 1

    logger.info(
        "✅ Stats pre-computation complete: %d cached, %d errors",
        total_computed,
        total_errors,
    )
