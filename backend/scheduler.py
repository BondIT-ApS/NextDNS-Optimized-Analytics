from apscheduler.schedulers.background import BackgroundScheduler
from models import add_log
import requests
import os

API_KEY = os.getenv("API_KEY")
PROFILE_ID = os.getenv("PROFILE_ID")
NEXTDNS_API_URL = f"https://api.nextdns.io/profiles/{PROFILE_ID}/logs"

def fetch_logs():
    headers = {"X-Api-Key": API_KEY}
    params = {"from": "-1h", "to": "now", "raw": "false"}
    response = requests.get(NEXTDNS_API_URL, headers=headers, params=params)
    if response.status_code == 200:
        logs = response.json().get("data", [])
        for log in logs:
            add_log(log)

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_logs, "interval", hours=1)
scheduler.start()
