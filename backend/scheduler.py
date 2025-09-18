# file: backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from models import add_log, get_total_record_count, get_last_fetch_timestamp, update_fetch_status
from datetime import datetime, timezone
import requests
import os
import sys

# Set up logging
from logging_config import get_logger
logger = get_logger(__name__)

API_KEY = os.getenv("API_KEY")
PROFILE_ID = os.getenv("PROFILE_ID")
FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", 60))  # Default to 60 minutes
FETCH_LIMIT = int(os.getenv("FETCH_LIMIT", 100))  # Default to 100 records per request

# Check if required variables are set
if not API_KEY or not PROFILE_ID:
    logger.warning("⚠️  Missing NextDNS API credentials!")
    logger.info("💡 Please set API_KEY and PROFILE_ID environment variables")
    logger.warning("🧱 Scheduler will not start - no logs will be fetched")
    scheduler = None
else:
    NEXTDNS_API_URL = f"https://api.nextdns.io/profiles/{PROFILE_ID}/logs"
    logger.info(f"✅ NextDNS API configured for profile: {PROFILE_ID}")

    def fetch_logs():
        """Fetch logs from NextDNS API with timestamp-based incremental fetching."""
        # Log initial database state
        initial_count = get_total_record_count()
        logger.info(f"🔄 Starting incremental NextDNS log fetch (Database has {initial_count:,} records)")
        
        try:
            # Get last fetch timestamp for incremental fetching
            last_fetch = get_last_fetch_timestamp(PROFILE_ID)
            
            headers = {"X-Api-Key": API_KEY}
            
            # Build parameters for incremental fetching
            if last_fetch:
                # Fetch records newer than last fetch (with small overlap for safety)
                from_time = last_fetch.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
                params = {"from": from_time, "to": "now", "raw": "false", "limit": FETCH_LIMIT}
                logger.info(f"📅 Incremental fetch from: {from_time} (last fetch: {last_fetch})")
            else:
                # First fetch - get last hour of data
                params = {"from": "-1h", "to": "now", "raw": "false", "limit": FETCH_LIMIT}
                logger.info(f"📅 Initial fetch: last {FETCH_LIMIT} records from past hour")
            
            logger.debug(f"🌐 Making API request to NextDNS: {NEXTDNS_API_URL}")
            logger.debug(f"🔧 Request params: {params}")
            response = requests.get(NEXTDNS_API_URL, headers=headers, params=params)
            
            if response.status_code == 200:
                logs = response.json().get("data", [])
                logger.info(f"🔄 Fetched {len(logs)} DNS logs from NextDNS API")
                
                if not logs:
                    logger.info(f"✅ No new records to process")
                    return
                
                # Process logs with duplicate tracking
                added_count = 0
                skipped_count = 0
                latest_timestamp = None
                
                for log in logs:
                    record_id, is_new = add_log(log)
                    if record_id:
                        if is_new:
                            added_count += 1
                            # Track the latest timestamp for incremental fetching
                            log_timestamp_str = log.get("timestamp")
                            if log_timestamp_str:
                                log_timestamp = datetime.fromisoformat(log_timestamp_str.replace('Z', '+00:00'))
                                if not latest_timestamp or log_timestamp > latest_timestamp:
                                    latest_timestamp = log_timestamp
                        else:
                            skipped_count += 1
                    else:
                        logger.warning(f"⚠️  Failed to process log for domain: {log.get('domain')}")
                
                # Update fetch status with latest timestamp
                if latest_timestamp and added_count > 0:
                    update_fetch_status(PROFILE_ID, latest_timestamp, added_count)
                    logger.debug(f"📅 Updated fetch status: latest_timestamp={latest_timestamp}")
                
                # Log comprehensive statistics
                final_count = get_total_record_count()
                
                logger.info(f"💾 Fetch completed: {added_count} NEW records added, {skipped_count} duplicates skipped")
                logger.info(f"📊 Database now has {final_count:,} total records (+{added_count:,} new this fetch)")
                
                if skipped_count > 0:
                    logger.info(f"🔄 Duplicate prevention working: {skipped_count}/{len(logs)} records were duplicates")
                    
            else:
                logger.error(f"⚠️  NextDNS API returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Error fetching NextDNS logs: {e}")
        except Exception as e:
            logger.error(f"❌ Unexpected error in fetch_logs: {e}")

    # Initialize and start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_logs, "interval", minutes=FETCH_INTERVAL)
    scheduler.start()
    logger.info(f"🔄 NextDNS log fetching scheduler started (runs every {FETCH_INTERVAL} minutes)")
    logger.info(f"🕰️ Fetch interval configured: {FETCH_INTERVAL} minutes ({FETCH_INTERVAL/60:.1f} hours)")
    logger.info(f"📊 Fetch limit configured: {FETCH_LIMIT} records per request")
