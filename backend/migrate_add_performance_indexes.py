"""
Database migration script to add performance optimization indexes.

This script adds the missing composite indexes identified in Issue #183
for improving query performance on large datasets (4M+ records).

Usage:
    python migrate_add_performance_indexes.py

New indexes added:
- idx_dns_logs_blocked_timestamp: (blocked, timestamp)
- idx_dns_logs_profile_blocked_timestamp: (profile_id, blocked, timestamp)
- idx_dns_logs_domain_blocked_timestamp: (domain, blocked, timestamp)

These indexes will be created CONCURRENTLY to avoid locking the table
in production environments (PostgreSQL only).
"""

import logging
import sys
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from models import engine, logger as models_logger

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def check_index_exists(connection, index_name: str) -> bool:
    """
    Check if an index already exists in the database.

    Args:
        connection: SQLAlchemy connection
        index_name: Name of the index to check

    Returns:
        bool: True if index exists, False otherwise
    """
    query = text("""
        SELECT EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE indexname = :index_name
        );
    """)
    result = connection.execute(query, {"index_name": index_name})
    return result.scalar()


def create_index_concurrently(connection, index_sql: str, index_name: str) -> bool:
    """
    Create an index using CONCURRENTLY to avoid table locking.

    Args:
        connection: SQLAlchemy connection
        index_sql: SQL statement to create the index
        index_name: Name of the index for logging

    Returns:
        bool: True if successful, False if index already exists or error occurred
    """
    try:
        # Check if index already exists
        if check_index_exists(connection, index_name):
            logger.info(f"✅ Index {index_name} already exists, skipping")
            return True

        logger.info(f"🔄 Creating index {index_name}...")

        # CONCURRENTLY requires committing the transaction first
        connection.commit()

        # Execute CREATE INDEX CONCURRENTLY
        connection.execute(text(index_sql))
        connection.commit()

        logger.info(f"✅ Successfully created index {index_name}")
        return True

    except ProgrammingError as e:
        if "already exists" in str(e).lower():
            logger.info(f"✅ Index {index_name} already exists")
            return True
        else:
            logger.error(f"❌ Error creating index {index_name}: {e}")
            return False
    except Exception as e:
        logger.error(f"❌ Unexpected error creating index {index_name}: {e}")
        return False


def main():
    """Main migration function to add performance indexes."""
    logger.info("🚀 Starting database migration: Add performance optimization indexes")
    logger.info("📋 This migration adds 3 composite indexes for Issue #183")

    # Define the indexes to create
    indexes = [
        {
            "name": "idx_dns_logs_blocked_timestamp",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_dns_logs_blocked_timestamp
                ON dns_logs (blocked, timestamp)
            """,
            "description": "Covering index for stats queries filtering by blocked status"
        },
        {
            "name": "idx_dns_logs_profile_blocked_timestamp",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_dns_logs_profile_blocked_timestamp
                ON dns_logs (profile_id, blocked, timestamp)
            """,
            "description": "Covering index for profile-filtered stats with blocked status"
        },
        {
            "name": "idx_dns_logs_domain_blocked_timestamp",
            "sql": """
                CREATE INDEX CONCURRENTLY idx_dns_logs_domain_blocked_timestamp
                ON dns_logs (domain, blocked, timestamp)
            """,
            "description": "Covering index for domain aggregations with blocked status"
        }
    ]

    success_count = 0
    total_count = len(indexes)

    try:
        # Get a connection with autocommit for CONCURRENTLY operations
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            logger.info(f"🗄️  Connected to database: {engine.url.database}")

            # Create each index
            for idx in indexes:
                logger.info(f"\n📊 {idx['description']}")
                if create_index_concurrently(connection, idx["sql"], idx["name"]):
                    success_count += 1

            # Run ANALYZE to update query planner statistics
            logger.info("\n🔍 Running ANALYZE to update query planner statistics...")
            connection.execute(text("ANALYZE dns_logs"))
            logger.info("✅ ANALYZE completed")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

    # Summary
    logger.info("\n" + "="*60)
    logger.info(f"📊 Migration Summary:")
    logger.info(f"   • Total indexes: {total_count}")
    logger.info(f"   • Successfully created/verified: {success_count}")
    logger.info(f"   • Failed: {total_count - success_count}")

    if success_count == total_count:
        logger.info("✅ Migration completed successfully!")
        logger.info("🚀 Database is now optimized for better query performance")
        sys.exit(0)
    else:
        logger.error("⚠️  Migration completed with errors")
        sys.exit(1)


if __name__ == "__main__":
    main()
