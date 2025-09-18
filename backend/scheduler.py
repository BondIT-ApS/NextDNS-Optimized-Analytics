# file: backend/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler
from models import add_log
import requests
import os
import sys

API_KEY = os.getenv("API_KEY")
PROFILE_ID = os.getenv("PROFILE_ID")

# Check if required variables are set
if not API_KEY or not PROFILE_ID:
    print("⚠️  Missing NextDNS API credentials!")
    print("💡 Please set API_KEY and PROFILE_ID environment variables")
    print("🧱 Scheduler will not start - no logs will be fetched")
    scheduler = None
else:
    NEXTDNS_API_URL = f"https://api.nextdns.io/profiles/{PROFILE_ID}/logs"
    print(f"✅ NextDNS API configured for profile: {PROFILE_ID}")

    def fetch_logs():
        """Fetch logs from NextDNS API and store them in the database."""
        try:
            headers = {"X-Api-Key": API_KEY}
            params = {"from": "-1h", "to": "now", "raw": "false"}
            response = requests.get(NEXTDNS_API_URL, headers=headers, params=params)
            
            if response.status_code == 200:
                logs = response.json().get("data", [])
                print(f"🔄 Fetched {len(logs)} new DNS logs from NextDNS")
                for log in logs:
                    add_log(log)
            else:
                print(f"⚠️  NextDNS API returned status {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Error fetching NextDNS logs: {e}")
        except Exception as e:
            print(f"❌ Unexpected error in fetch_logs: {e}")

    # Initialize and start scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(fetch_logs, "interval", hours=1)
    scheduler.start()
    print("🔄 NextDNS log fetching scheduler started (runs every hour)")
