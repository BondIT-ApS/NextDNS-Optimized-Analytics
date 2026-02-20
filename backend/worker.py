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

import os
import signal
import sys
import threading

# Set up logging first
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)

# Graceful shutdown via threading.Event (avoids sys.exit in signal handler)
shutdown_event = threading.Event()


def signal_handler(signum, _frame):
    """Handle shutdown signals gracefully."""
    signal_name = signal.Signals(signum).name
    logger.info(f"🛑 Received {signal_name}, shutting down worker gracefully...")
    shutdown_event.set()


def main():
    """Run the NextDNS log fetch scheduler as a standalone worker process."""
    logger.info("🚀 Starting NextDNS Analytics Worker")
    logger.info("📋 Worker runs DNS log fetch scheduler only (no HTTP server)")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Initialize database connection and seed config from env if needed
    logger.info("🗄️  Initializing database connection...")
    try:
        from models import init_db, migrate_config_from_env

        init_db()
        logger.info("✅ Database connection initialized")
        if migrate_config_from_env():
            logger.info("🔑 Config seeded from environment variables")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        sys.exit(1)

    # Import and start the scheduler
    logger.info("🔄 Starting NextDNS log fetch scheduler...")
    try:
        from scheduler import scheduler  # pylint: disable=unused-import

        logger.info("✅ Scheduler started successfully")

        # Log scheduler configuration (reads from DB)
        from models import get_nextdns_api_key, get_active_profile_ids

        fetch_interval = int(os.getenv("FETCH_INTERVAL", "60"))
        api_key_configured = bool(get_nextdns_api_key())
        active_profiles = get_active_profile_ids()

        logger.info(f"⏰ Fetch interval: {fetch_interval} minutes")
        logger.info(f"🔑 API Key configured: {api_key_configured}")
        logger.info(f"📊 Monitoring {len(active_profiles)} active profile(s)")

        if not api_key_configured or not active_profiles:
            logger.warning(
                "⚠️  Worker started but NextDNS API credentials"
                " not fully configured"
            )
            logger.warning(
                "⚠️  Scheduler will not fetch logs until" " credentials are set"
            )
            logger.warning(
                "💡 Use PUT /settings/nextdns/api-key"
                " and POST /settings/nextdns/profiles"
            )

    except ImportError as e:
        logger.error(f"❌ Failed to import scheduler: {e}")
        logger.error(
            "❌ Ensure scheduler.py is present and all dependencies are installed"
        )
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Failed to start scheduler: {e}")
        sys.exit(1)

    # Keep the worker running until shutdown signal
    logger.info("✅ Worker is running and healthy")
    logger.info("🔄 Scheduler will fetch logs according to configured interval")

    while not shutdown_event.is_set():
        shutdown_event.wait(60)  # Wake every 60s or on signal
        if not shutdown_event.is_set():
            # Periodic health check log (only in DEBUG mode)
            if os.getenv("LOG_LEVEL", "INFO").upper() == "DEBUG":
                logger.debug("💓 Worker heartbeat: scheduler running")

    logger.info("🛑 Worker stopped gracefully")


if __name__ == "__main__":
    main()
