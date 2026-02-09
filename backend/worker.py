#!/usr/bin/env python3
"""
NextDNS Analytics Worker Process

Standalone worker that runs the DNS log fetch scheduler.
Used in Kubernetes multi-pod deployments to avoid scheduler conflicts.

Usage:
    python worker.py

Environment Variables:
    - All standard NextDNS configuration (API_KEY, PROFILE_IDS, etc.)
    - FETCH_INTERVAL: Scheduler interval in minutes (default: 60)
    - LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR)

Deployment Modes:
    - Docker Compose: Not needed (scheduler runs in backend container)
    - K8s Single-Pod: Not needed (scheduler runs in backend pod)
    - K8s Multi-Pod: Use this worker (deploy as separate single-replica pod)
"""

import logging
import os
import signal
import sys
import time

# Set up logging first
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"🛑 Received {signal_name}, shutting down worker gracefully...")
    sys.exit(0)


def main():
    """Run the NextDNS log fetch scheduler as a standalone worker process."""
    logger.info("🚀 Starting NextDNS Analytics Worker")
    logger.info("📋 Worker runs DNS log fetch scheduler only (no HTTP server)")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database connection
    logger.info("🗄️  Initializing database connection...")
    try:
        from models import init_db

        init_db()
        logger.info("✅ Database connection initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Import and start the scheduler
    logger.info("🔄 Starting NextDNS log fetch scheduler...")
    try:
        from scheduler import scheduler

        logger.info("✅ Scheduler started successfully")

        # Get scheduler interval from environment
        fetch_interval = int(os.getenv("FETCH_INTERVAL", "60"))
        logger.info(f"⏰ Fetch interval: {fetch_interval} minutes")

        # Log scheduler configuration
        api_key_configured = bool(os.getenv("API_KEY"))
        profile_ids = os.getenv("PROFILE_IDS", "")
        profile_count = len(profile_ids.split(",")) if profile_ids else 0

        logger.info(f"🔑 API Key configured: {api_key_configured}")
        logger.info(f"📊 Monitoring {profile_count} profile(s)")

        if not api_key_configured or profile_count == 0:
            logger.warning(
                "⚠️  Worker started but NextDNS API credentials not configured"
            )
            logger.warning("⚠️  Scheduler will not fetch logs until credentials are set")

    except ImportError as e:
        logger.error(f"❌ Failed to import scheduler: {e}")
        logger.error(
            "❌ Ensure scheduler.py is present and all dependencies are installed"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        sys.exit(1)

    # Keep the worker running
    logger.info("✅ Worker is running and healthy")
    logger.info("🔄 Scheduler will fetch logs according to configured interval")
    logger.info("💡 Press Ctrl+C to stop the worker")

    try:
        # Keep the main thread alive
        while True:
            time.sleep(60)  # Sleep for 1 minute
            # Periodic health check log (only in DEBUG mode)
            if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG":
                logger.debug("💓 Worker heartbeat: scheduler running")

    except KeyboardInterrupt:
        logger.info("🛑 Worker stopped by user (KeyboardInterrupt)")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ Worker crashed with unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
