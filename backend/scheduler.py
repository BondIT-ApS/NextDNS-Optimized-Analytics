# file: backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from models import add_log, get_total_record_count
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
        """Fetch logs from NextDNS API and store them in the database."""
        # Log initial database state
        initial_count = get_total_record_count()
        logger.info(f"🔄 Starting NextDNS log fetch (Database has {initial_count:,} records)")
        
        try:
            headers = {"X-Api-Key": API_KEY}
            params = {"from": "-1h", "to": "now", "raw": "false", "limit": FETCH_LIMIT}
            
            logger.debug(f"🌐 Making API request to NextDNS: {NEXTDNS_API_URL}")
            response = requests.get(NEXTDNS_API_URL, headers=headers, params=params)
            
            if response.status_code == 200:
                logs = response.json().get("data", [])
                logger.info(f"🔄 Fetched {len(logs)} DNS logs from NextDNS API")
                
                added_count = 0
                skipped_count = 0
                for log in logs:
                    result = add_log(log)
                    if result:
                        added_count += 1
                    else:
                        skipped_count += 1
                
                # Log final statistics
                final_count = get_total_record_count()
                new_records = final_count - initial_count
                
                logger.info(f"💾 Fetch completed: {added_count} added, {skipped_count} skipped")
                logger.info(f"📊 Database now has {final_count:,} total records (+{new_records:,} new)")
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
