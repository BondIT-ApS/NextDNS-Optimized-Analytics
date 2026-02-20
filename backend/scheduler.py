# file: backend/scheduler.py  # pylint: disable=duplicate-code
import os
from datetime import datetime

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from models import (
    add_log,
    get_total_record_count,
    get_last_fetch_timestamp,
    update_fetch_status,
    get_nextdns_api_key,
    get_active_profile_ids,
    get_fetch_limit,
)

# Set up logging
from logging_config import get_logger

logger = get_logger(__name__)

FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))  # Default to 60 minutes
# FETCH_LIMIT is read from DB on each cycle via get_fetch_limit()


def fetch_logs():  # pylint: disable=too-many-locals,too-many-branches,too-many-statements,too-many-nested-blocks
    """Fetch logs from NextDNS API with timestamp-based incremental fetching for multiple profiles.

    API key and profile list are read from the database on every invocation so
    that changes made via the settings API take effect on the next scheduled
    run without requiring a restart.
    """
    # Re-read config from DB on every cycle (supports dynamic management)
    api_key = get_nextdns_api_key()
    profile_ids = get_active_profile_ids()
    fetch_limit = get_fetch_limit()

    if not api_key or not profile_ids:
        logger.warning("⚠️  Missing NextDNS API credentials — skipping fetch cycle")
        if not api_key:
            logger.info("💡 Set the API key via PUT /settings/nextdns/api-key")
        if not profile_ids:
            logger.info("💡 Add profiles via POST /settings/nextdns/profiles")
        return

    # Log initial database state
    initial_count = get_total_record_count()
    logger.info(
        f"🔄 Starting multi-profile NextDNS log fetch (Database has {initial_count:,} records)"
    )

    total_added = 0
    total_skipped = 0
    successful_profiles = 0
    failed_profiles = 0

    # Fetch from each profile
    for profile_id in profile_ids:  # pylint: disable=too-many-nested-blocks
        try:
            logger.info(f"🧱 Processing profile: {profile_id}")

            # Get last fetch timestamp for this specific profile
            last_fetch = get_last_fetch_timestamp(profile_id)

            headers = {"X-Api-Key": api_key}
            nextdns_api_url = f"https://api.nextdns.io/profiles/{profile_id}/logs"

            # Build parameters for incremental fetching
            if last_fetch:
                # Fetch records newer than last fetch (with small overlap for safety)
                from_time = last_fetch.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
                params = {
                    "from": from_time,
                    "to": "now",
                    "raw": "false",
                    "limit": fetch_limit,
                }
                logger.info(
                    f"📅 Profile {profile_id}: incremental fetch from {from_time}"
                )
            else:
                # First fetch - get last hour of data
                params = {
                    "from": "-1h",
                    "to": "now",
                    "raw": "false",
                    "limit": fetch_limit,
                }
                logger.info(f"📅 Profile {profile_id}: initial fetch from past hour")

            logger.debug(f"🌐 Making API request to: {nextdns_api_url}")
            response = requests.get(nextdns_api_url, headers=headers, params=params)

            if response.status_code == 200:
                logs = response.json().get("data", [])
                logger.info(f"🔄 Profile {profile_id}: fetched {len(logs)} DNS logs")

                if not logs:
                    logger.info(
                        f"✅ Profile {profile_id}: no new records to process"
                    )
                    successful_profiles += 1
                    continue

                # Process logs with duplicate tracking
                profile_added = 0
                profile_skipped = 0
                latest_timestamp = None

                for log in logs:
                    # Ensure the log has the profile_id tagged
                    log["profile_id"] = profile_id

                    record_id, is_new = add_log(log)
                    if record_id:
                        if is_new:
                            profile_added += 1
                            # Track the latest timestamp for incremental fetching
                            log_timestamp_str = log.get("timestamp")
                            if log_timestamp_str:
                                log_timestamp = datetime.fromisoformat(
                                    log_timestamp_str.replace("Z", "+00:00")
                                )
                                if (
                                    not latest_timestamp
                                    or log_timestamp > latest_timestamp
                                ):
                                    latest_timestamp = log_timestamp
                        else:
                            profile_skipped += 1
                    else:
                        logger.warning(
                            f"⚠️  Profile {profile_id}: failed to process log "
                            f"for domain: {log.get('domain')}"
                        )

                # Update fetch status with latest timestamp for this profile
                if latest_timestamp and profile_added > 0:
                    update_fetch_status(profile_id, latest_timestamp, profile_added)
                    logger.debug(f"📅 Profile {profile_id}: updated fetch status")

                # Log profile statistics
                logger.info(
                    f"💾 Profile {profile_id}: {profile_added} NEW records added, "
                    f"{profile_skipped} duplicates skipped"
                )

                total_added += profile_added
                total_skipped += profile_skipped
                successful_profiles += 1

            else:
                logger.error(
                    f"⚠️  Profile {profile_id}: API returned status "
                    f"{response.status_code}: {response.text}"
                )
                failed_profiles += 1

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Profile {profile_id}: error fetching logs: {e}")
            failed_profiles += 1
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"❌ Profile {profile_id}: unexpected error: {e}")
            failed_profiles += 1

    # Log comprehensive statistics for all profiles
    final_count = get_total_record_count()
    logger.info("🏁 Multi-profile fetch completed:")
    logger.info(
        f"📊 Total: {total_added} NEW records added, {total_skipped} duplicates skipped"
    )
    logger.info(
        f"📊 Profiles: {successful_profiles} successful, {failed_profiles} failed"
    )
    logger.info(
        f"📊 Database now has {final_count:,} total records (+{total_added:,} new this fetch)"
    )

    if total_skipped > 0:
        logger.info("🔄 Duplicate prevention working across all profiles")


# Initialize and start scheduler
scheduler = BackgroundScheduler()  # pylint: disable=invalid-name
scheduler.add_job(fetch_logs, "interval", minutes=FETCH_INTERVAL, id="fetch_logs")
scheduler.start()
logger.info(
    f"🔄 NextDNS log fetching scheduler started (runs every {FETCH_INTERVAL} minutes)"
)
logger.info(
    f"🕰️ Fetch interval configured: {FETCH_INTERVAL} minutes ({FETCH_INTERVAL/60:.1f} hours)"
)
logger.info("📊 Fetch limit is read from DB on each fetch cycle")
logger.info(
    "🧱 API key, profiles and fetch limit are read from DB on each fetch cycle"
)
