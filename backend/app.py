# file: backend/app.py
import os

from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from models import init_db, get_logs, get_logs_stats

# Set up logging first
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Import scheduler to start NextDNS log fetching
try:
    from scheduler import scheduler  # pylint: disable=unused-import,duplicate-code

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
    search_query = request.args.get("search", "")
    status_filter = request.args.get("status", "all")  # all, blocked, allowed
    limit = int(request.args.get("limit", 100))

    logger.debug(
        f"📊 API request for logs with exclude_domains: {exclude_domains}, "
        f"search: '{search_query}', status: {status_filter}, limit: {limit}"
    )

    log_results = get_logs(
        exclude_domains=exclude_domains,
        search_query=search_query,
        status_filter=status_filter,
        limit=limit,
    )

    logger.info(f"📊 Returning {len(log_results)} DNS logs")
    return jsonify({"data": log_results})


@app.route("/logs/stats", methods=["GET"])
@auth.login_required
def logs_stats():
    """Get total statistics for all logs in the database."""

    logger.debug("📊 API request for logs statistics")
    stats = get_logs_stats()
    logger.info(f"📊 Returning stats: {stats}")
    return jsonify(stats)


if __name__ == "__main__":
    logger.info("🚀 Starting NextDNS Optimized Analytics Backend")
    init_db()  # Ensure the database is initialized
    logger.info("🖥️  Starting Flask server on 0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000)
