#!/usr/bin/env python3
"""
Database management script for NextDNS Optimized Analytics

This script provides easy commands for managing database migrations using Alembic.
Like having a LEGO instruction manual for your database schema!

Migration files follow the pattern: YYYY_MM_DD_<revision_id>_<description>.py
Example: 2025_09_18_5eef40b793b3_initial_postgresql_schema_with_enhanced_dns_logs.py

Usage:
    python manage_db.py init     # Initialize database with current schema
    python manage_db.py upgrade  # Upgrade to latest schema version
    python manage_db.py status   # Show current migration status
    python manage_db.py history  # Show migration history

Note: Make sure PostgreSQL is running and environment variables are set!
"""

import os
import sys
import subprocess
from pathlib import Path

# Set up logging
from logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def run_alembic_command(command_args):
    """Run an Alembic command with proper error handling."""
    try:
        cmd = ["alembic"] + command_args
        logger.info(f"🧱 Running: {' '.join(cmd)}")
        result = subprocess.run(
            cmd, cwd=Path(__file__).parent, check=True, capture_output=True, text=True
        )
        logger.info(result.stdout)
        if result.stderr:
            logger.warning(f"⚠️ Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error running Alembic command: {e}")
        logger.debug(f"stdout: {e.stdout}")
        logger.debug(f"stderr: {e.stderr}")
        return False


def check_environment():
    """Check if required environment variables are set."""
    # Database connection variables (required for migrations)
    db_vars = ["POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB", "POSTGRES_HOST"]
    # NextDNS API variables (optional for migrations, but needed for the app to work)
    # Note: API_KEY and PROFILE_IDS are seeded into the database on first boot.
    # They can also be managed dynamically via PUT /settings/nextdns/api-key
    # and POST /settings/nextdns/profiles after startup.
    api_vars = ["LOCAL_API_KEY"]

    missing_db_vars = []
    missing_api_vars = []

    for var in db_vars:
        if not os.getenv(var):
            missing_db_vars.append(var)

    for var in api_vars:
        if not os.getenv(var):
            missing_api_vars.append(var)

    if missing_db_vars:
        logger.error(
            f"❌ Missing required database variables: {', '.join(missing_db_vars)}"
        )
        logger.info("💡 Make sure to set these variables or load your .env file")
        return False

    if missing_api_vars:
        logger.warning(
            f"⚠️  Missing NextDNS API variables: {', '.join(missing_api_vars)}"
        )
        logger.info("💡 These are needed for the application to fetch NextDNS logs")
        logger.info("🧱 Database migrations will work, but the app won't fetch logs")

    logger.info("✅ Database environment variables are properly configured")
    if not missing_api_vars:
        logger.info("✅ NextDNS API environment variables are properly configured")

    return True


def init_database():
    """Initialize the database with the latest schema."""
    logger.info("🏧️ Initializing database schema...")
    if not check_environment():
        return False

    return run_alembic_command(["upgrade", "head"])


def upgrade_database():
    """Upgrade database to the latest schema."""
    logger.info("⬆️ Upgrading database schema...")
    if not check_environment():
        return False

    return run_alembic_command(["upgrade", "head"])


def show_status():
    """Show current migration status."""
    logger.info("📊 Checking migration status...")
    if not check_environment():
        return False

    return run_alembic_command(["current"])


def show_history():
    """Show migration history."""
    logger.info("📜 Migration history:")
    return run_alembic_command(["history"])


def main():
    """Main CLI interface."""
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)

    command = sys.argv[1].lower()

    commands = {
        "init": init_database,
        "upgrade": upgrade_database,
        "status": show_status,
        "history": show_history,
    }

    if command not in commands:
        logger.error(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)

    logger.info("🧱 NextDNS Optimized Analytics - Database Management")
    logger.info("=" * 50)

    success = commands[command]()

    if success:
        logger.info("✅ Command completed successfully!")
    else:
        logger.error("❌ Command failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
