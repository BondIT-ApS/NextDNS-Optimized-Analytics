# file: backend/app.py
from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from models import init_db, get_logs, add_log
import os

# Set up logging first
from logging_config import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import scheduler to start NextDNS log fetching
try:
    from scheduler import scheduler
    logger.info("🔄 NextDNS log scheduler started successfully")
except ImportError as e:
    logger.warning(f"⚠️  Could not start scheduler: {e}")
    logger.info("🧱 App will work but won't automatically fetch NextDNS logs")

app = Flask(__name__)
auth = HTTPBasicAuth()

# API Key for authentication
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY")

users = {"admin": LOCAL_API_KEY}

@auth.verify_password
def verify_password(username, password):
    return username in users and users[username] == password

@app.route("/logs", methods=["GET"])
@auth.login_required
def logs():
    exclude_domains = request.args.getlist("exclude")
    logger.debug(f"📊 API request for logs with exclude_domains: {exclude_domains}")
    logs = get_logs(exclude_domains)
    logger.info(f"📊 Returning {len(logs)} DNS logs")
    return jsonify({"data": logs})

if __name__ == "__main__":
    logger.info("🚀 Starting NextDNS Optimized Analytics Backend")
    init_db()  # Ensure the database is initialized
    logger.info("🖥️  Starting Flask server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
