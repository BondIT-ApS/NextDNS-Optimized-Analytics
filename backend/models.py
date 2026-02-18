# file: backend/models.py
import json
import os
import re
from datetime import datetime, timezone, timedelta
from typing import Optional

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    Index,
    TypeDecorator,
    UniqueConstraint,
    func,
    text,
    or_,
)
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
from logging_config import get_logger

logger = get_logger(__name__)


# Helper function for TLD extraction
def extract_tld(domain):
    """Extract top-level domain from a full domain name using regex.

    Examples:
        gateway.icloud.com -> icloud.com
        bag.itunes.apple.com -> apple.com
        www.google.com -> google.com
        gateway.fe2.apple-dns.net -> apple-dns.net

    Args:
        domain (str): Full domain name

    Returns:
        str: Top-level domain or original domain if extraction fails

    # TODO: Consider using tldextract library for more accurate TLD extraction
    # that handles complex TLDs like .co.uk, .com.au properly
    """
    if not domain or not isinstance(domain, str):
        return domain

    try:
        # Simple regex approach: extract the last two parts of the domain
        # This works for most common cases but won't handle complex TLDs
        match = re.match(r"^(?:.*\.)?(\w[\w-]*\.[a-zA-Z]{2,})$", domain.lower())
        if match:
            return match.group(1)
        return domain
    except (AttributeError, IndexError) as e:
        logger.debug(f"Failed to extract TLD from '{domain}': {e}")
        return domain


def build_domain_exclusion_filter(domain_column, exclude_domains):
    """Build SQL filter conditions for domain exclusion with wildcard support.

    Converts wildcard patterns to SQL LIKE patterns and combines with exact matches.
    Supports patterns like:
        - *.apple.com → Matches icloud.apple.com, www.apple.com
        - apple.* → Matches apple.com, apple.net, apple.org
        - *tracking* → Matches any domain containing 'tracking'

    Args:
        domain_column: SQLAlchemy column object (e.g., DNSLog.domain)
        exclude_domains (list): List of domains/patterns to exclude

    Returns:
        SQLAlchemy filter condition (and_/or_ expression) or None if no exclusions

    Examples:
        >>> filter_cond = build_domain_exclusion_filter(DNSLog.domain, ['*.apple.com', 'google.com'])
        >>> query = query.filter(filter_cond)
    """
    if not exclude_domains or len(exclude_domains) == 0:
        return None

    # Separate exact matches from wildcard patterns
    exact_matches = []
    wildcard_conditions = []

    for pattern in exclude_domains:
        if not pattern or not isinstance(pattern, str):
            continue

        pattern = pattern.strip()
        if not pattern:
            continue

        # Check if pattern contains wildcard
        if "*" in pattern:
            # Validate pattern - reject overly broad patterns for performance
            if pattern == "*" or pattern == "**" or pattern == "*.*":
                logger.warning(
                    f"⚠️ Rejecting overly broad wildcard pattern: '{pattern}'"
                )
                continue

            # Convert wildcard pattern to SQL LIKE pattern
            # Escape SQL LIKE special characters first
            sql_pattern = pattern.replace("_", "\\_").replace("%", "\\%")
            # Replace * with SQL LIKE %
            sql_pattern = sql_pattern.replace("*", "%")

            # Add condition for this pattern (case-insensitive)
            wildcard_conditions.append(domain_column.ilike(sql_pattern))
            logger.debug(
                f"🔍 Wildcard pattern: '{pattern}' → SQL ILIKE '{sql_pattern}'"
            )
        else:
            # Exact match
            exact_matches.append(pattern)

    # Build combined filter conditions
    conditions = []

    # Add exact match exclusion (case-insensitive using lowercase comparison)
    if exact_matches:
        # Convert patterns to lowercase for case-insensitive matching
        lowercase_patterns = [p.lower() for p in exact_matches]
        conditions.append(~func.lower(domain_column).in_(lowercase_patterns))
        logger.debug(
            f"🚫 Excluding {len(exact_matches)} exact domain matches (case-insensitive)"
        )

    # Add wildcard exclusions (using NOT LIKE for each)
    if wildcard_conditions:
        # Combine all wildcard conditions with OR, then negate
        # NOT (pattern1 OR pattern2) = domain doesn't match any pattern
        combined_wildcards = or_(*wildcard_conditions)
        conditions.append(~combined_wildcards)
        logger.debug(f"🔍 Excluding {len(wildcard_conditions)} wildcard patterns")

    # Combine all conditions with AND
    if len(conditions) == 0:
        return None
    elif len(conditions) == 1:
        return conditions[0]
    else:
        # Both exact and wildcard conditions exist
        from sqlalchemy import and_

        return and_(*conditions)


# Custom Text type that forces TEXT without JSON casting
class ForceText(TypeDecorator):  # pylint: disable=too-many-ancestors
    """Custom SQLAlchemy type that forces values to be stored as text."""

    impl = Text
    cache_ok = True  # SQLAlchemy 1.4+ requirement

    def process_bind_param(self, value, dialect):  # pylint: disable=unused-argument
        if value is not None:
            return str(value)
        return value

    def process_result_value(
        self, value, dialect
    ):  # pylint: disable=unused-argument
        return value

    def process_literal_param(
        self, value, dialect
    ):  # pylint: disable=unused-argument
        """Process literal parameter for SQL compilation."""
        return str(value) if value is not None else value

    @property
    def python_type(self):
        """Return the Python type object expected by this type."""
        return str


# Base declaration
Base = declarative_base()

# Database connection setup
DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT', '5432')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

# Add SSL mode if specified (required for managed databases like DigitalOcean)
# Supports both PGSSLMODE (standard PostgreSQL) and POSTGRES_SSL_MODE
ssl_mode = os.getenv("PGSSLMODE") or os.getenv("POSTGRES_SSL_MODE", "")
if ssl_mode:
    DATABASE_URL += f"?sslmode={ssl_mode}"

engine = create_engine(DATABASE_URL, echo=False)
session_factory = sessionmaker(bind=engine)


# Database model for DNS logs
class DNSLog(Base):
    """Model representing a DNS log entry from NextDNS."""

    __tablename__ = "dns_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    action = Column(
        String(50), nullable=True, default="default"
    )  # allowed, blocked, etc.
    device = Column(ForceText, nullable=True)  # Store device info as JSON string
    client_ip = Column(String(45))  # Support IPv4 and IPv6
    query_type = Column(String(10), default="A")  # A, AAAA, CNAME, etc.
    blocked = Column(Boolean, default=False, nullable=False, index=True)
    profile_id = Column(String(50), index=True)
    tld = Column(
        String(255), nullable=True
    )  # Computed TLD for fast aggregation (Phase 3)
    data = Column(
        ForceText, nullable=False
    )  # Store original raw data as JSON string
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Add composite indexes and unique constraint for duplicate prevention
    __table_args__ = (
        Index("idx_dns_logs_timestamp_domain", "timestamp", "domain"),
        Index("idx_dns_logs_domain_action", "domain", "action"),
        Index("idx_dns_logs_profile_timestamp", "profile_id", "timestamp"),
        # Unique constraint to prevent duplicates based on
        # timestamp, domain, and client_ip
        UniqueConstraint(
            "timestamp",
            "domain",
            "client_ip",
            name="uq_dns_logs_timestamp_domain_client",
        ),
    )


# Database model for tracking fetch progress
class FetchStatus(Base):
    """Model for tracking DNS log fetch progress and status."""

    __tablename__ = "fetch_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    last_fetch_timestamp = Column(DateTime(timezone=True), nullable=False)
    last_successful_fetch = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    records_fetched = Column(Integer, default=0, nullable=False)
    profile_id = Column(String(50), nullable=False, index=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        # Ensure we only have one status record per profile
        UniqueConstraint("profile_id", name="uq_fetch_status_profile"),
    )


# Check database connectivity for health checks
def check_database_health():
    """Check if database is accessible and healthy.

    Uses a lightweight SELECT 1 query instead of COUNT(*) to avoid
    expensive full table scans on large tables (8M+ rows).

    Returns:
        bool: True if database is accessible

    Raises:
        SQLAlchemyError: If database is not accessible
    """
    session = session_factory()
    try:
        # Lightweight connectivity check - no table scan
        session.execute(text("SELECT 1"))
        logger.debug("✅ Database health check passed (connectivity OK)")
        return True
    finally:
        session.close()


# Get total record count from database (estimated)
def get_total_record_count():
    """Get the estimated number of DNS log records in the database.

    Uses PostgreSQL's pg_class.reltuples for a fast estimated count
    instead of COUNT(*) which requires a full table scan.
    The estimate is updated by VACUUM and ANALYZE operations.

    Returns:
        int: Estimated number of records, or 0 if error occurs
    """
    session = session_factory()
    try:
        result = session.execute(
            text(
                "SELECT COALESCE(reltuples, 0)::bigint "
                "FROM pg_class WHERE relname = 'dns_logs'"
            )
        )
        row = result.fetchone()
        count = row[0] if row else 0
        # reltuples can be -1 if stats haven't been collected yet
        count = max(count, 0)
        logger.debug(
            f"📊 Database contains ~{count:,} total DNS log records (estimated)"
        )
        return count
    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting record count: {e}")
        return 0
    finally:
        session.close()


# Initialize the database (now handled by Alembic migrations)
def init_db():
    # Note: Database initialization is now handled by Alembic migrations
    # Run 'alembic upgrade head' to initialize/update the database schema
    logger.info("🗄 Database initialization is handled by Alembic migrations.")
    logger.info(
        "🔄 Run 'alembic upgrade head' to ensure database schema is up to date."
    )

    # Log current database status
    total_records = get_total_record_count()
    logger.info(f"💾 Database currently contains {total_records:,} DNS log records")


# Add log entry to the database with duplicate prevention
def add_log(log):
    """Add a DNS log entry to the database with duplicate prevention.

    Args:
        log (dict): DNS log data containing domain, action, device, and other fields

    Returns:
        tuple: (record_id, is_new) where record_id is the ID and
        is_new indicates if it's a new record
    """
    session = session_factory()
    try:
        # Extract timestamp from log data
        log_timestamp_str = log.get("timestamp")
        if log_timestamp_str:
            # Parse NextDNS timestamp format: 2025-09-18T08:11:39.673Z
            log_timestamp = datetime.fromisoformat(
                log_timestamp_str.replace("Z", "+00:00")
            )
        else:
            log_timestamp = datetime.now(timezone.utc)

        # Determine action based on NextDNS log structure
        action = log.get("action") or log.get("status") or "default"

        # Handle device - extract name if it's a dict, otherwise use as is
        device_info = log.get("device")

        # Handle client info - could be in clientIp field
        client_ip = log.get("client_ip") or log.get("clientIp")

        # Check for existing record first (duplicate prevention)
        existing_log = (
            session.query(DNSLog)
            .filter_by(
                timestamp=log_timestamp,
                domain=log.get("domain"),
                client_ip=client_ip,
            )
            .first()
        )

        if existing_log:
            logger.debug(
                f"🔄 Duplicate found for domain {log.get('domain')} "
                f"at {log_timestamp} - skipping"
            )
            return existing_log.id, False  # Return existing ID, not new

        # Determine if request was blocked
        blocked = (
            log.get("blocked", False)
            or action == "blocked"
            or log.get("status") == "blocked"
        )

        # Ensure all JSON data is properly serialized as strings
        device_str = json.dumps(device_info) if device_info else None
        data_str = json.dumps(log) if isinstance(log, dict) else str(log)

        # Debug output to check data types (only in DEBUG mode)
        logger.debug(
            f"🐛 Data serialization - device type: {type(device_str)}, device value: {device_str}"
        )
        logger.debug(
            f"🐛 Data serialization - data type: {type(data_str)}, "
            f"data value (first 100 chars): {str(data_str)[:100]}"
        )

        # Extract TLD for Phase 3 optimization
        domain = log.get("domain")
        tld = extract_tld(domain) if domain else None

        new_log = DNSLog(
            timestamp=log_timestamp,
            domain=domain,
            action=action,
            device=device_str,
            client_ip=client_ip,
            query_type=log.get("query_type", "A"),
            blocked=blocked,
            profile_id=log.get("profile_id"),
            tld=tld,  # Phase 3: Pre-computed TLD for fast aggregation
            data=data_str,
        )
        session.add(new_log)
        session.commit()
        logger.debug(
            f"💾 Successfully added NEW log for domain: {log.get('domain')} at {log_timestamp}"
        )
        return new_log.id, True  # Return new ID, is new
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error adding log to database: {e}")
        return None, False
    finally:
        session.close()


# Get last fetch timestamp for incremental fetching
def get_last_fetch_timestamp(profile_id):
    """Get the last successful fetch timestamp for a profile.

    Args:
        profile_id (str): NextDNS profile ID

    Returns:
        datetime: Last fetch timestamp or None if no previous fetch
    """
    session = session_factory()
    try:
        fetch_status = (
            session.query(FetchStatus).filter_by(profile_id=profile_id).first()
        )
        if fetch_status:
            logger.debug(
                f"📅 Last fetch for profile {profile_id}: {fetch_status.last_fetch_timestamp}"
            )
            return fetch_status.last_fetch_timestamp

        logger.debug(f"📅 No previous fetch found for profile {profile_id}")
        return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting last fetch timestamp: {e}")
        return None
    finally:
        session.close()


# Update fetch status after successful fetch
# pylint: disable=too-many-positional-arguments
def update_fetch_status(profile_id, last_timestamp, records_count):
    """Update or create fetch status record.

    Args:
        profile_id (str): NextDNS profile ID
        last_timestamp (datetime): Timestamp of the last fetched record
        records_count (int): Number of records fetched in this batch
    """
    session = session_factory()
    try:
        fetch_status = (
            session.query(FetchStatus).filter_by(profile_id=profile_id).first()
        )

        if fetch_status:
            # Update existing record
            fetch_status.last_fetch_timestamp = last_timestamp
            fetch_status.last_successful_fetch = datetime.now(timezone.utc)
            fetch_status.records_fetched += records_count
            fetch_status.updated_at = datetime.now(timezone.utc)
            logger.debug(
                f"📅 Updated fetch status for profile {profile_id}: "
                f"last_timestamp={last_timestamp}, "
                f"total_records={fetch_status.records_fetched}"
            )
        else:
            # Create new record
            fetch_status = FetchStatus(
                profile_id=profile_id,
                last_fetch_timestamp=last_timestamp,
                records_fetched=records_count,
            )
            session.add(fetch_status)
            logger.debug(
                f"📅 Created new fetch status for profile {profile_id}: "
                f"last_timestamp={last_timestamp}, records={records_count}"
            )

        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error updating fetch status: {e}")
        return False
    finally:
        session.close()


# Retrieve logs with optional exclusion of domains and advanced filtering
def get_logs(  # pylint: disable=too-many-positional-arguments,too-many-locals,too-many-branches
    exclude_domains=None,
    search_query="",
    status_filter="all",
    profile_filter=None,
    device_filter=None,
    time_range="all",
    limit=100,
    offset=0,
):
    """Retrieve DNS logs with optional filtering and pagination.

    Args:
        exclude_domains (list): List of domains to exclude from results
        search_query (str): Domain name search query
        status_filter (str): Filter by status - 'all', 'blocked', 'allowed'
        profile_filter (str): Filter by specific profile ID
        device_filter (list): List of device names to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip for pagination

    Returns:
        tuple: (list of DNS log dictionaries, filtered total count)
    """
    logger.debug(
        f"📊 Retrieving logs with limit={limit}, offset={offset}, "
        f"exclude_domains={exclude_domains}, search='{search_query}', "
        f"status='{status_filter}', profile='{profile_filter}', "
        f"devices={device_filter}, time_range='{time_range}'"
    )
    session = session_factory()
    try:
        query = session.query(DNSLog).order_by(DNSLog.timestamp.desc())

        # Apply domain exclusions (with wildcard support)
        if exclude_domains:
            exclusion_filter = build_domain_exclusion_filter(
                DNSLog.domain, exclude_domains
            )
            if exclusion_filter is not None:
                query = query.filter(exclusion_filter)

        # Apply search filter on domain name
        if search_query.strip():
            query = query.filter(DNSLog.domain.ilike(f"%{search_query}%"))
            logger.debug(f"🔍 Filtering by domain search: '{search_query}'")

        # Apply status filter (case-insensitive)
        if status_filter and status_filter.lower() == "blocked":
            query = query.filter(DNSLog.blocked.is_(True))
            logger.debug("🚫 Filtering for blocked requests only")
        elif status_filter and status_filter.lower() == "allowed":
            query = query.filter(DNSLog.blocked.is_(False))
            logger.debug("✅ Filtering for allowed requests only")

        # Apply profile filter
        if profile_filter and profile_filter.strip():
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Filtering for profile: '{profile_filter}'")

        # Apply device filter
        if device_filter and len(device_filter) > 0:
            # Filter logs based on device names
            device_conditions = []
            for device_name in device_filter:
                if device_name.strip():
                    # Check for devices where the JSON device field contains the name
                    device_conditions.append(
                        DNSLog.device.ilike(f'%"name": "{device_name}"%')
                    )
            if device_conditions:
                query = query.filter(or_(*device_conditions))
                logger.debug(f"📱 Filtering for devices: {device_filter}")

        # Apply time range filter
        if time_range != "all":
            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)
                logger.debug(f"📅 Filtering for time range: {time_range}")

        # Get filtered total count before applying pagination
        filtered_total_records = query.count()
        logger.info(
            f"📊 Database query: requesting {limit} records from {filtered_total_records:,} filtered records"
        )

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "domain": log.domain,
                "action": log.action,
                "device": (
                    json.loads(log.device)
                    if log.device and isinstance(log.device, str)
                    else log.device
                ),
                "client_ip": log.client_ip,
                "query_type": log.query_type,
                "blocked": log.blocked,
                "profile_id": log.profile_id,
                "data": (
                    json.loads(log.data)
                    if log.data and isinstance(log.data, str)
                    else log.data
                ),
                "created_at": log.created_at.isoformat(),
            }
            for log in query.all()
        ]
        logger.debug(f"📊 Retrieved {len(result)} logs from database")
        return result, filtered_total_records
    except SQLAlchemyError as e:
        logger.error(f"❌ Error retrieving logs from database: {e}")
        return [], 0
    finally:
        session.close()


# Get total statistics for all logs in the database
def get_logs_stats(profile_filter=None, time_range="all", exclude_domains=None):
    """Get statistics for DNS logs in the database, optionally filtered by profile and time range.

    Args:
        profile_filter (str): Optional profile ID to filter statistics
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        exclude_domains (list): List of domains/patterns to exclude from statistics

    Returns:
        dict: Dictionary containing total, blocked, and allowed counts and percentages
    """
    session = session_factory()
    try:
        query = session.query(DNSLog)

        # Apply domain exclusions (with wildcard support)
        if exclude_domains:
            exclusion_filter = build_domain_exclusion_filter(
                DNSLog.domain, exclude_domains
            )
            if exclusion_filter is not None:
                query = query.filter(exclusion_filter)

        # Apply profile filter if specified
        if profile_filter and profile_filter.strip():
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Getting stats for profile: '{profile_filter}'")

        # Apply time range filter
        if time_range != "all":
            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)
                logger.debug(f"📅 Getting stats for time range: {time_range}")

        # Get total count
        total_count = query.count()

        # Get blocked count
        blocked_count = query.filter(DNSLog.blocked is True).count()

        # Calculate allowed count
        allowed_count = total_count - blocked_count

        # Calculate percentages
        blocked_percentage = (
            (blocked_count / total_count * 100) if total_count > 0 else 0
        )
        allowed_percentage = (
            (allowed_count / total_count * 100) if total_count > 0 else 0
        )

        stats = {
            "total": total_count,
            "blocked": blocked_count,
            "allowed": allowed_count,
            "blocked_percentage": round(blocked_percentage, 1),
            "allowed_percentage": round(allowed_percentage, 1),
            "profile_id": profile_filter,
        }

        logger.debug(f"📊 Database stats: {stats}")
        return stats
    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting logs statistics: {e}")
        return {
            "total": 0,
            "blocked": 0,
            "allowed": 0,
            "blocked_percentage": 0,
            "allowed_percentage": 0,
            "profile_id": profile_filter,
        }
    finally:
        session.close()


# Get list of available profiles in the database
def get_available_profiles():
    """Get list of profile IDs that have data in the database.

    Returns:
        list: List of profile IDs with record counts
    """
    session = session_factory()
    try:
        # Query for distinct profile IDs and their counts

        # pylint: disable=not-callable
        results = (
            session.query(
                DNSLog.profile_id,
                func.count(DNSLog.id).label("record_count"),
                func.max(DNSLog.timestamp).label("last_activity"),
            )
            .filter(DNSLog.profile_id.isnot(None))
            .group_by(DNSLog.profile_id)
            .order_by(func.count(DNSLog.id).desc())
            .all()
        )
        # pylint: enable=not-callable

        profiles = []
        for result in results:
            profiles.append(
                {
                    "profile_id": result.profile_id,
                    "record_count": result.record_count,
                    "last_activity": (
                        result.last_activity.isoformat()
                        if result.last_activity
                        else None
                    ),
                }
            )

        logger.debug(f"🧱 Found {len(profiles)} profiles with data")
        return profiles
    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting available profiles: {e}")
        return []
    finally:
        session.close()


# Get real stats overview data from database
def get_stats_overview(
    profile_filter=None, time_range="24h", exclude_domains=None
):  # pylint: disable=too-many-locals,too-many-branches
    """Get overview statistics from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        exclude_domains (list): List of domains/patterns to exclude from statistics

    Returns:
        dict: Statistics overview
    """
    session = session_factory()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply domain exclusions (with wildcard support)
        if exclude_domains:
            exclusion_filter = build_domain_exclusion_filter(
                DNSLog.domain, exclude_domains
            )
            if exclusion_filter is not None:
                query = query.filter(exclusion_filter)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Filtering stats for profile: '{profile_filter}'")

        # Apply time range filter
        if time_range != "all":

            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),  # 3 months = ~90 days
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)
                logger.debug(f"📅 Filtering for time range: {time_range}")

        # Get total queries
        total_queries = query.count()

        # Get blocked queries
        blocked_queries = query.filter(DNSLog.blocked.is_(True)).count()

        # Calculate allowed queries and percentage
        allowed_queries = total_queries - blocked_queries
        blocked_percentage = (
            (blocked_queries / total_queries * 100) if total_queries > 0 else 0
        )

        # Calculate queries per hour (rough estimate)
        hours_map = {
            "30m": 0.5,
            "1h": 1,
            "6h": 6,
            "24h": 24,
            "7d": 168,
            "30d": 720,
            "3m": 2160,  # 90 days * 24 hours
            "all": 1,
        }
        hours = hours_map.get(time_range, 24)
        queries_per_hour = total_queries / hours if hours > 0 else 0

        # Get most active device (simplified approach for now)
        most_active_device = None
        try:
            # Try to get device name from the most recent record with a device
            recent_device_log = query.filter(DNSLog.device.isnot(None)).first()
            if recent_device_log and recent_device_log.device:
                device_data = (
                    json.loads(recent_device_log.device)
                    if isinstance(recent_device_log.device, str)
                    else recent_device_log.device
                )
                if device_data and "name" in device_data:
                    most_active_device = device_data["name"]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            logger.debug(f"Could not determine most active device: {e}")
            most_active_device = None

        # Get top blocked domain (only if there are blocked queries and use same filters)
        top_blocked_domain = None
        if blocked_queries > 0:
            try:
                # Use the same filtered query with profile and time range filters applied
                # We need to build a new query with the same filters for aggregation
                blocked_domain_query = session.query(
                    DNSLog.domain,
                    func.count(DNSLog.id).label(
                        "count"
                    ),  # pylint: disable=not-callable
                )

                # Apply the same profile filter
                if (
                    profile_filter
                    and profile_filter.strip()
                    and profile_filter != "all"
                ):
                    blocked_domain_query = blocked_domain_query.filter(
                        DNSLog.profile_id == profile_filter
                    )

                # Apply the same time range filter
                if time_range != "all":
                    if time_range in time_deltas:
                        blocked_domain_query = blocked_domain_query.filter(
                            DNSLog.timestamp >= cutoff_time
                        )

                # pylint: disable=not-callable
                blocked_domain_result = (
                    blocked_domain_query.filter(DNSLog.blocked.is_(True))
                    .group_by(DNSLog.domain)
                    .order_by(func.count(DNSLog.id).desc())
                    .first()
                )
                # pylint: enable=not-callable
                if blocked_domain_result and blocked_domain_result[0]:
                    top_blocked_domain = blocked_domain_result[0]
            except SQLAlchemyError as e:
                logger.debug(f"Could not determine top blocked domain: {e}")
                top_blocked_domain = None

        stats = {
            "total_queries": total_queries,
            "blocked_queries": blocked_queries,
            "allowed_queries": allowed_queries,
            "blocked_percentage": round(blocked_percentage, 1),
            "queries_per_hour": round(queries_per_hour, 1),
            "most_active_device": most_active_device,
            "top_blocked_domain": top_blocked_domain,
        }

        logger.debug(f"📊 Real stats overview: {stats}")
        return stats

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting stats overview: {e}")
        return {
            "total_queries": 0,
            "blocked_queries": 0,
            "allowed_queries": 0,
            "blocked_percentage": 0.0,
            "queries_per_hour": 0.0,
            "most_active_device": None,
            "top_blocked_domain": None,
        }
    finally:
        session.close()


# Get time series data from database
def get_stats_timeseries(
    profile_filter=None, time_range="24h", granularity="hour", group_by="status"
):  # pylint: disable=too-many-locals,too-many-branches,too-many-statements
    """Get time series statistics from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        granularity (str): Time granularity (hour, day, etc.)
        group_by (str): Grouping mode - "status" (blocked/allowed) or "profile" (by profile_id)

    Returns:
        list or dict: List of time series data points (status mode) or dict with data and
                      available_profiles (profile mode)
    """
    session = session_factory()
    try:

        now = datetime.now(timezone.utc)

        # Initialize variables to avoid unbound local variable error
        interval_minutes = 0
        interval_hours = 0
        display_time = None

        # For 'all' time range, we need to query the actual data range from the database
        earliest_timestamp = None
        if time_range == "all":
            # Query the earliest timestamp in the database
            earliest_query = session.query(func.min(DNSLog.timestamp))

            # Apply profile filter if specified
            if profile_filter and profile_filter.strip() and profile_filter != "all":
                earliest_query = earliest_query.filter(
                    DNSLog.profile_id == profile_filter
                )

            earliest_timestamp = earliest_query.scalar()

            # If no data exists, use last 30 days as fallback
            if earliest_timestamp is None:
                logger.warning(
                    "⚠️ No data found in database for 'all' time range, using 30-day fallback"
                )
                earliest_timestamp = now - timedelta(days=29)

        # Determine time parameters based on time range
        if time_range == "30m":
            start_time = now - timedelta(minutes=30)
            interval_minutes = 1
            num_intervals = 30  # 30 x 1min = 30 minutes
            granularity = "1min"
        elif time_range == "1h":
            start_time = now - timedelta(hours=1)
            interval_minutes = 5
            num_intervals = 12  # 12 x 5min = 1 hour
            granularity = "5min"
        elif time_range == "6h":
            start_time = now - timedelta(hours=6)
            interval_minutes = 15
            num_intervals = 24  # 24 x 15min = 6 hours
            granularity = "15min"
        elif time_range == "24h":
            start_time = now - timedelta(hours=24)
            interval_hours = 1
            num_intervals = 24  # 24 x 1hour = 24 hours
            granularity = "hour"
        elif time_range == "7d":
            # For daily data, align to start of today and work backwards
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_time = today_start - timedelta(
                days=6
            )  # 6 days back + today = 7 days
            interval_hours = 24
            num_intervals = 7  # 7 x 1day = 7 days
            granularity = "day"
        elif time_range == "30d":
            # For daily data, align to start of today and work backwards
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_time = today_start - timedelta(
                days=29
            )  # 29 days back + today = 30 days
            interval_hours = 24
            num_intervals = 30  # 30 x 1day = 30 days
            granularity = "day"
        elif time_range == "3m":
            # For 3 months, use weekly intervals
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            # Go back to the start of the week (Monday)
            days_since_monday = today_start.weekday()
            week_start = today_start - timedelta(days=days_since_monday)
            start_time = week_start - timedelta(
                weeks=12
            )  # 12 weeks back + current week = ~3 months
            interval_hours = 24 * 7  # 1 week = 168 hours
            num_intervals = 13  # 13 x 1week = ~3 months
            granularity = "week"
        else:  # 'all'
            # For 'all', use the actual data range from the database
            # Align to start of day for clean boundaries
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            earliest_day = earliest_timestamp.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # Calculate total days of data
            total_days = (today_start - earliest_day).days + 1

            logger.info(
                "📅 'all' time range: %d days of data (from %s to %s)",
                total_days,
                earliest_day.date(),
                today_start.date(),
            )

            # Choose granularity based on data range
            if total_days <= 90:
                # Up to 90 days: use daily granularity
                start_time = earliest_day
                interval_hours = 24
                num_intervals = total_days
                granularity = "day"
                logger.debug("📊 Using daily granularity for %d days", total_days)
            else:
                # More than 90 days: use weekly granularity
                # Align to start of week (Monday)
                days_since_monday = earliest_day.weekday()
                week_start = earliest_day - timedelta(days=days_since_monday)
                start_time = week_start

                # Calculate number of weeks
                days_to_cover = (today_start - week_start).days + 1
                num_intervals = (days_to_cover + 6) // 7  # Round up to nearest week
                interval_hours = 24 * 7
                granularity = "week"
                logger.debug(
                    "📊 Using weekly granularity for %d days (%d weeks)",
                    total_days,
                    num_intervals,
                )

        # Build base query
        base_query = session.query(DNSLog).filter(DNSLog.timestamp >= start_time)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            base_query = base_query.filter(DNSLog.profile_id == profile_filter)

        # Generate time buckets
        data_points = []
        for i in range(num_intervals):
            if time_range in ["30m", "1h", "6h"]:
                interval_start = start_time + timedelta(minutes=i * interval_minutes)
                interval_end = interval_start + timedelta(minutes=interval_minutes)
                # Round to appropriate intervals for clean display
                if time_range == "30m":
                    # Round to exact minute
                    display_time = interval_start.replace(second=0, microsecond=0)
                elif time_range == "1h":
                    # Round to nearest 5 minutes
                    display_time = interval_start.replace(
                        minute=(interval_start.minute // 5) * 5,
                        second=0,
                        microsecond=0,
                    )
                elif time_range == "6h":
                    # Round to nearest 15 minutes
                    display_time = interval_start.replace(
                        minute=(interval_start.minute // 15) * 15,
                        second=0,
                        microsecond=0,
                    )
            else:
                interval_start = start_time + timedelta(hours=i * interval_hours)
                interval_end = interval_start + timedelta(hours=interval_hours)

                if granularity == "hour":
                    # Round to exact hour for clean display
                    display_time = interval_start.replace(
                        minute=0, second=0, microsecond=0
                    )
                elif granularity == "week":
                    # For weekly granularity, use the start of the week (Monday)
                    display_time = interval_start.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )
                else:  # day
                    # For daily granularity, use the start of the interval
                    # Since we've aligned intervals to start of day, this gives correct dates
                    display_time = interval_start.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )

            # Query for this interval
            interval_query = base_query.filter(
                DNSLog.timestamp >= interval_start, DNSLog.timestamp < interval_end
            )

            if group_by == "profile":
                # Group by profile_id within this time interval
                profile_counts = {}
                profile_query = (
                    interval_query.with_entities(
                        DNSLog.profile_id,
                        func.count(DNSLog.id),  # pylint: disable=not-callable
                    )
                    .group_by(DNSLog.profile_id)
                    .all()
                )

                total_queries = 0
                for profile_id, count in profile_query:
                    if profile_id:  # Skip None profile_ids
                        profile_counts[profile_id] = count
                        total_queries += count

                data_points.append(
                    {
                        "timestamp": display_time.isoformat(),
                        "total_queries": total_queries,
                        "profiles": profile_counts,
                    }
                )
            else:
                # Default: group by status (blocked/allowed)
                total_queries = interval_query.count()
                blocked_queries = interval_query.filter(
                    DNSLog.blocked.is_(True)
                ).count()
                allowed_queries = total_queries - blocked_queries

                data_points.append(
                    {
                        "timestamp": display_time.isoformat(),
                        "total_queries": total_queries,
                        "blocked_queries": blocked_queries,
                        "allowed_queries": allowed_queries,
                    }
                )

        logger.debug(
            f"📊 Generated {len(data_points)} {granularity} time series data points for {time_range}"
        )

        # Debug: Log first and last data points to verify timestamp alignment
        if data_points and granularity == "day":
            first_point = data_points[0]
            last_point = data_points[-1]
            logger.debug(
                f"🕐 First data point: {first_point['timestamp']} ({first_point['total_queries']} queries)"
            )
            logger.debug(
                f"🕐 Last data point: {last_point['timestamp']} ({last_point['total_queries']} queries)"
            )

        # Return format depends on grouping mode
        if group_by == "profile":
            # Get list of all available profiles from the query
            all_profiles = (
                base_query.with_entities(DNSLog.profile_id).distinct().all()
            )
            available_profiles = [p[0] for p in all_profiles if p[0]]

            return {
                "data": data_points,
                "granularity": granularity,
                "total_points": len(data_points),
                "available_profiles": available_profiles,
            }

        # Legacy format: return list directly
        return data_points

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting time series data: {e}")
        if group_by == "profile":
            return {
                "data": [],
                "granularity": granularity,
                "total_points": 0,
                "available_profiles": [],
            }
        return []
    finally:
        session.close()


# Get top domains from database
def get_top_domains(
    profile_filter=None, time_range="24h", limit=10, exclude_domains=None
):  # pylint: disable=too-many-locals
    """Get top blocked and allowed domains from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        limit (int): Number of top domains to return
        exclude_domains (list): List of domains/patterns to exclude from results

    Returns:
        dict: Contains blocked_domains and allowed_domains lists
    """
    session = session_factory()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply domain exclusions (with wildcard support)
        if exclude_domains:
            exclusion_filter = build_domain_exclusion_filter(
                DNSLog.domain, exclude_domains
            )
            if exclusion_filter is not None:
                query = query.filter(exclusion_filter)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)

        # Apply time range filter
        if time_range != "all":

            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),  # 3 months = ~90 days
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)

        # Get total queries for percentage calculation
        total_queries = query.count()

        # Get top blocked domains
        blocked_domains = []
        if total_queries > 0:
            try:
                # pylint: disable=not-callable
                blocked_results = (
                    query.with_entities(
                        DNSLog.domain, func.count(DNSLog.id).label("count")
                    )
                    .filter(DNSLog.blocked.is_(True))
                    .group_by(DNSLog.domain)
                    .order_by(func.count(DNSLog.id).desc())
                    .limit(limit)
                    .all()
                )
                # pylint: enable=not-callable

                for domain_result in blocked_results:
                    domain_name = domain_result[0]
                    count = domain_result[1]
                    percentage = (
                        (count / total_queries * 100) if total_queries > 0 else 0
                    )
                    blocked_domains.append(
                        {
                            "domain": domain_name,
                            "count": count,
                            "percentage": round(percentage, 1),
                        }
                    )
            except SQLAlchemyError as e:
                logger.error(f"Error getting blocked domains: {e}")

        # Get top allowed domains
        allowed_domains = []
        if total_queries > 0:
            try:
                # pylint: disable=not-callable
                allowed_results = (
                    query.with_entities(
                        DNSLog.domain, func.count(DNSLog.id).label("count")
                    )
                    .filter(DNSLog.blocked.is_(False))
                    .group_by(DNSLog.domain)
                    .order_by(func.count(DNSLog.id).desc())
                    .limit(limit)
                    .all()
                )
                # pylint: enable=not-callable

                for domain_result in allowed_results:
                    domain_name = domain_result[0]
                    count = domain_result[1]
                    percentage = (
                        (count / total_queries * 100) if total_queries > 0 else 0
                    )
                    allowed_domains.append(
                        {
                            "domain": domain_name,
                            "count": count,
                            "percentage": round(percentage, 1),
                        }
                    )
            except SQLAlchemyError as e:
                logger.error(f"Error getting allowed domains: {e}")

        result = {
            "blocked_domains": blocked_domains,
            "allowed_domains": allowed_domains,
        }

        logger.debug(
            f"📊 Found {len(blocked_domains)} blocked and {len(allowed_domains)} allowed top domains"
        )
        return result

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting top domains: {e}")
        return {"blocked_domains": [], "allowed_domains": []}
    finally:
        session.close()


# Get top-level domains (TLD aggregation) from database
def get_stats_tlds(  # pylint: disable=too-many-locals,too-many-branches
    profile_filter=None, time_range="24h", limit=10, exclude_domains=None
):
    """Get top-level domain statistics aggregated from full domains.

    Groups all subdomains under their parent domains (TLD).
    Examples: gateway.icloud.com -> icloud.com

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        limit (int): Number of top TLDs to return
        exclude_domains (list): List of domains/patterns to exclude from results

    Returns:
        dict: Contains blocked_tlds and allowed_tlds lists
    """
    session = session_factory()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply domain exclusions (with wildcard support)
        if exclude_domains:
            exclusion_filter = build_domain_exclusion_filter(
                DNSLog.domain, exclude_domains
            )
            if exclusion_filter is not None:
                query = query.filter(exclusion_filter)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)

        # Apply time range filter
        if time_range != "all":
            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)

        # Phase 3 Optimization: Use database-side aggregation with TLD column
        # This eliminates the need to load all records into Python and extract TLDs

        # Get total queries for percentage calculation
        total_queries = query.count()

        # Aggregate blocked TLDs using database GROUP BY
        # pylint: disable=not-callable
        blocked_results = (
            query.with_entities(DNSLog.tld, func.count(DNSLog.id).label("count"))
            .filter(DNSLog.blocked.is_(True))
            .filter(DNSLog.tld.isnot(None))  # Exclude null TLDs
            .group_by(DNSLog.tld)
            .order_by(func.count(DNSLog.id).desc())
            .limit(limit)
            .all()
        )

        # Aggregate allowed TLDs using database GROUP BY
        allowed_results = (
            query.with_entities(DNSLog.tld, func.count(DNSLog.id).label("count"))
            .filter(DNSLog.blocked.is_(False))
            .filter(DNSLog.tld.isnot(None))  # Exclude null TLDs
            .group_by(DNSLog.tld)
            .order_by(func.count(DNSLog.id).desc())
            .limit(limit)
            .all()
        )
        # pylint: enable=not-callable

        # Format blocked TLDs
        blocked_tlds = []
        for tld_result in blocked_results:
            tld = tld_result[0]
            count = tld_result[1]
            percentage = (count / total_queries * 100) if total_queries > 0 else 0
            blocked_tlds.append(
                {
                    "domain": tld,
                    "count": count,
                    "percentage": round(percentage, 1),
                }
            )

        # Format allowed TLDs
        allowed_tlds = []
        for tld_result in allowed_results:
            tld = tld_result[0]
            count = tld_result[1]
            percentage = (count / total_queries * 100) if total_queries > 0 else 0
            allowed_tlds.append(
                {
                    "domain": tld,
                    "count": count,
                    "percentage": round(percentage, 1),
                }
            )

        result = {
            "blocked_tlds": blocked_tlds,
            "allowed_tlds": allowed_tlds,
        }

        logger.debug(
            f"📊 Found {len(blocked_tlds)} blocked and {len(allowed_tlds)} allowed top TLDs"
        )
        return result

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting TLD statistics: {e}")
        return {"blocked_tlds": [], "allowed_tlds": []}
    finally:
        session.close()


# Get device usage statistics from database
def get_stats_devices(  # pylint: disable=too-many-locals,too-many-branches
    profile_filter=None,
    time_range="24h",
    limit=10,
    exclude_devices=None,
    exclude_domains=None,
):
    """Get device usage statistics showing DNS query activity by device.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
                         - 30m: Last 30 minutes (1-minute granularity)
                         - 6h: Last 6 hours (15-minute granularity)
                         - 3m: Last 3 months (weekly granularity)
        limit (int): Number of top devices to return
        exclude_devices (list): List of device names to exclude from results
        exclude_domains (list): List of domain patterns to exclude (supports wildcards)

    Returns:
        list: List of device statistics with usage information
    """
    session = session_factory()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)

        # Apply domain exclusion filter
        domain_filter = build_domain_exclusion_filter(DNSLog.domain, exclude_domains)
        if domain_filter is not None:
            query = query.filter(domain_filter)

        # Apply time range filter
        if time_range != "all":
            now = datetime.now(timezone.utc)

            time_deltas = {
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "6h": timedelta(hours=6),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
                "3m": timedelta(days=90),
            }

            if time_range in time_deltas:
                cutoff_time = now - time_deltas[time_range]
                query = query.filter(DNSLog.timestamp >= cutoff_time)

        # Get all logs and aggregate by device
        all_logs = query.all()

        # Aggregate by device name
        device_stats = {}  # device_name -> {blocked, allowed, total, last_activity}

        for log_entry in all_logs:
            # Extract device name from JSON device field
            device_name = "Unidentified Device"  # Default

            if log_entry.device:
                try:
                    device_data = (
                        json.loads(log_entry.device)
                        if isinstance(log_entry.device, str)
                        else log_entry.device
                    )
                    if isinstance(device_data, dict) and "name" in device_data:
                        device_name = device_data["name"] or "Unidentified Device"
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Keep default "Unidentified Device"
                    pass

            # Apply device exclusion filter (case-insensitive)
            if exclude_devices:
                exclude_lower = [name.lower() for name in exclude_devices]
                if device_name.lower() in exclude_lower:
                    continue

            # Initialize device stats if not exists
            if device_name not in device_stats:
                device_stats[device_name] = {
                    "blocked": 0,
                    "allowed": 0,
                    "total": 0,
                    "last_activity": log_entry.timestamp,
                }

            # Update stats
            if log_entry.blocked:
                device_stats[device_name]["blocked"] += 1
            else:
                device_stats[device_name]["allowed"] += 1
            device_stats[device_name]["total"] += 1

            # Update last activity if this log is more recent
            if log_entry.timestamp > device_stats[device_name]["last_activity"]:
                device_stats[device_name]["last_activity"] = log_entry.timestamp

        # Format and sort results
        device_results = []
        for device_name, stats in device_stats.items():
            blocked_percentage = (
                (stats["blocked"] / stats["total"] * 100)
                if stats["total"] > 0
                else 0
            )
            allowed_percentage = (
                (stats["allowed"] / stats["total"] * 100)
                if stats["total"] > 0
                else 0
            )

            device_results.append(
                {
                    "device_name": device_name,
                    "total_queries": stats["total"],
                    "blocked_queries": stats["blocked"],
                    "allowed_queries": stats["allowed"],
                    "blocked_percentage": round(blocked_percentage, 1),
                    "allowed_percentage": round(allowed_percentage, 1),
                    "last_activity": stats["last_activity"].isoformat(),
                }
            )

        # Sort by total queries (most active first) and limit results
        device_results.sort(key=lambda x: x["total_queries"], reverse=True)
        device_results = device_results[:limit]

        logger.debug(f"📱 Found {len(device_results)} devices with DNS activity")
        return device_results

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting device statistics: {e}")
        return []
    finally:
        session.close()


# Database metrics collection functions for PostgreSQL monitoring
def get_database_metrics():  # pylint: disable=too-many-branches,too-many-statements
    """Get comprehensive PostgreSQL database metrics.

    Returns:
        dict: Database metrics including connections, performance, and health
    """
    session = session_factory()
    try:
        # Initialize metrics structure
        metrics = {
            "connections": {"active": 0, "total": 0, "usage_percent": 0.0},
            "performance": {
                "cache_hit_ratio": 0.0,
                "database_size_mb": 0,
                "total_queries": 0,
            },
            "health": {"status": "unknown", "uptime_seconds": 0},
        }

        # Get connection statistics
        try:
            connection_stats = session.execute(
                text(
                    "SELECT count(*) as active_connections "
                    "FROM pg_stat_activity "
                    "WHERE state = 'active'"
                )
            ).fetchone()

            total_connections = session.execute(
                text("SELECT count(*) as total_connections FROM pg_stat_activity")
            ).fetchone()

            max_connections = session.execute(
                text("SHOW max_connections")
            ).fetchone()

            if connection_stats and total_connections and max_connections:
                active = connection_stats[0]
                total = total_connections[0]
                max_conn = int(max_connections[0])

                metrics["connections"]["active"] = active
                metrics["connections"]["total"] = total
                metrics["connections"]["max_connections"] = max_conn
                metrics["connections"]["usage_percent"] = round(
                    (total / max_conn * 100) if max_conn > 0 else 0, 1
                )

        except SQLAlchemyError as e:
            logger.debug(f"Could not fetch connection statistics: {e}")

        # Get cache hit ratio - using a more reliable query
        try:
            cache_stats = session.execute(
                text(
                    "SELECT "
                    "  CASE WHEN (sum(heap_blks_hit) + sum(heap_blks_read)) > 0 "
                    "       THEN round(sum(heap_blks_hit)::numeric / "
                    "            (sum(heap_blks_hit) + sum(heap_blks_read)), 3) "
                    "       ELSE 0.95 "
                    "  END as hit_ratio "
                    "FROM pg_statio_user_tables "
                    "WHERE schemaname = 'public'"
                )
            ).fetchone()

            if cache_stats and cache_stats[0] is not None:
                metrics["performance"]["cache_hit_ratio"] = float(cache_stats[0])
            else:
                # Default to a reasonable cache hit ratio if no data available
                metrics["performance"]["cache_hit_ratio"] = 0.95

        except SQLAlchemyError as e:
            logger.debug(f"Could not fetch cache hit ratio: {e}")
            metrics["performance"]["cache_hit_ratio"] = 0.95

        # Get database size
        try:
            db_size = session.execute(
                text("SELECT pg_database_size(current_database()) as size")
            ).fetchone()

            if db_size and db_size[0]:
                size_bytes = int(db_size[0])
                metrics["performance"]["database_size_mb"] = round(
                    size_bytes / (1024 * 1024), 1
                )
            else:
                metrics["performance"]["database_size_mb"] = 0

        except SQLAlchemyError as e:
            logger.debug(f"Could not fetch database size: {e}")
            metrics["performance"]["database_size_mb"] = 0

        # Get total queries (from our DNS logs table)
        try:
            total_queries = session.query(DNSLog).count()
            metrics["performance"]["total_queries"] = total_queries

        except SQLAlchemyError as e:
            logger.debug(f"Could not fetch total queries: {e}")

        # Get database uptime
        try:
            uptime_result = session.execute(
                text(
                    "SELECT EXTRACT(EPOCH FROM (now() - pg_postmaster_start_time())) as uptime"
                )
            ).fetchone()

            if uptime_result and uptime_result[0]:
                metrics["health"]["uptime_seconds"] = int(uptime_result[0])

        except SQLAlchemyError as e:
            logger.debug(f"Could not fetch database uptime: {e}")

        # Determine overall health status
        if (
            metrics["connections"]["usage_percent"] < 80
            and metrics["performance"]["cache_hit_ratio"] > 0.8
        ):
            metrics["health"]["status"] = "healthy"
        elif metrics["connections"]["usage_percent"] < 95:
            metrics["health"]["status"] = "warning"
        else:
            metrics["health"]["status"] = "critical"

        logger.debug(f"📊 Database metrics collected: {metrics}")
        return metrics

    except (SQLAlchemyError, ValueError, TypeError) as e:
        logger.error(f"❌ Error collecting database metrics: {e}")
        return {
            "connections": {"active": 0, "total": 0, "usage_percent": 0.0},
            "performance": {
                "cache_hit_ratio": 0.0,
                "database_size_mb": 0,
                "total_queries": 0,
            },
            "health": {"status": "error", "uptime_seconds": 0},
        }
    finally:
        session.close()


# ---------------------------------------------------------------------------
# System Settings — generic key/value store (shared foundation with #115)
# ---------------------------------------------------------------------------


class SystemSetting(Base):
    """Generic key/value settings table.

    Used to store application-level configuration that previously lived in
    environment variables.  The first key populated here is ``nextdns_api_key``;
    additional keys will be added in issue #115 (general system settings).
    """

    __tablename__ = "system_settings"

    key = Column(String(100), primary_key=True)
    value = Column(Text, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# NextDNS Profiles — managed profile list (replaces PROFILE_IDS env var)
# ---------------------------------------------------------------------------


class NextDNSProfile(Base):
    """Stores the set of NextDNS profiles the scheduler should fetch.

    Profiles are managed via the ``/settings/nextdns/profiles`` API rather
    than the ``PROFILE_IDS`` environment variable.  The env var is still read
    on first boot to seed this table (see ``migrate_config_from_env``).
    """

    __tablename__ = "nextdns_profiles"

    profile_id = Column(String(50), primary_key=True)
    enabled = Column(Boolean, default=True, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ---------------------------------------------------------------------------
# Generic settings helpers
# ---------------------------------------------------------------------------


def get_setting(key: str) -> Optional[str]:
    """Return the value for *key* from system_settings, or None."""
    session = session_factory()
    try:
        row = session.query(SystemSetting).filter_by(key=key).first()
        return row.value if row else None
    except SQLAlchemyError as e:
        logger.error(f"❌ Error reading setting '{key}': {e}")
        return None
    finally:
        session.close()


def set_setting(key: str, value: str) -> bool:
    """Upsert *key* → *value* in system_settings."""
    session = session_factory()
    try:
        row = session.query(SystemSetting).filter_by(key=key).first()
        if row:
            row.value = value
            row.updated_at = datetime.now(timezone.utc)
        else:
            row = SystemSetting(key=key, value=value)
            session.add(row)
        session.commit()
        logger.debug(f"✅ Setting '{key}' saved")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error saving setting '{key}': {e}")
        return False
    finally:
        session.close()


# ---------------------------------------------------------------------------
# NextDNS API key helpers
# ---------------------------------------------------------------------------

NEXTDNS_API_KEY_SETTING = "nextdns_api_key"


def get_nextdns_api_key() -> Optional[str]:
    """Return the stored NextDNS API key, or fall back to the env var."""
    key = get_setting(NEXTDNS_API_KEY_SETTING)
    if key:
        return key
    # Fallback: env var (used before first migration or in legacy setups)
    return os.getenv("API_KEY")


def set_nextdns_api_key(api_key: str) -> bool:
    """Persist the NextDNS API key to the database."""
    return set_setting(NEXTDNS_API_KEY_SETTING, api_key)


# ---------------------------------------------------------------------------
# NextDNS profile helpers
# ---------------------------------------------------------------------------


def get_active_profile_ids() -> list:
    """Return profile_ids for all *enabled* profiles in the DB.

    Falls back to env var ``PROFILE_IDS`` if the table is empty (e.g. before
    the first ``migrate_config_from_env`` run).
    """
    session = session_factory()
    try:
        rows = (
            session.query(NextDNSProfile)
            .filter_by(enabled=True)
            .order_by(NextDNSProfile.profile_id)
            .all()
        )
        if rows:
            return [r.profile_id for r in rows]
    except SQLAlchemyError as e:
        logger.error(f"❌ Error reading active profiles: {e}")
    finally:
        session.close()

    # Fallback to env var
    env_ids = os.getenv("PROFILE_IDS", "")
    return [p.strip() for p in env_ids.split(",") if p.strip()]


def get_all_profiles() -> list:
    """Return all NextDNSProfile rows (enabled and disabled)."""
    session = session_factory()
    try:
        return (
            session.query(NextDNSProfile).order_by(NextDNSProfile.profile_id).all()
        )
    except SQLAlchemyError as e:
        logger.error(f"❌ Error reading profiles: {e}")
        return []
    finally:
        session.close()


def get_profile(profile_id: str) -> Optional[object]:
    """Return a single NextDNSProfile row or None."""
    session = session_factory()
    try:
        return session.query(NextDNSProfile).filter_by(profile_id=profile_id).first()
    except SQLAlchemyError as e:
        logger.error(f"❌ Error reading profile '{profile_id}': {e}")
        return None
    finally:
        session.close()


def add_profile(profile_id: str) -> bool:
    """Insert a new enabled profile.  Returns False if it already exists."""
    session = session_factory()
    try:
        existing = (
            session.query(NextDNSProfile).filter_by(profile_id=profile_id).first()
        )
        if existing:
            logger.warning(f"⚠️  Profile '{profile_id}' already exists")
            return False
        session.add(NextDNSProfile(profile_id=profile_id, enabled=True))
        session.commit()
        logger.info(f"✅ Profile '{profile_id}' added")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error adding profile '{profile_id}': {e}")
        return False
    finally:
        session.close()


def update_profile_enabled(profile_id: str, enabled: bool) -> bool:
    """Enable or disable a profile.  Returns False if not found."""
    session = session_factory()
    try:
        row = session.query(NextDNSProfile).filter_by(profile_id=profile_id).first()
        if not row:
            return False
        row.enabled = enabled
        row.updated_at = datetime.now(timezone.utc)
        session.commit()
        state = "enabled" if enabled else "disabled"
        logger.info(f"✅ Profile '{profile_id}' {state}")
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error updating profile '{profile_id}': {e}")
        return False
    finally:
        session.close()


def delete_profile_data(profile_id: str) -> dict:
    """Remove all DNS logs and fetch status for *profile_id*.

    Returns a dict with counts of deleted rows per table.
    """
    session = session_factory()
    try:
        logs_deleted = (
            session.query(DNSLog)
            .filter(DNSLog.profile_id == profile_id)
            .delete(synchronize_session=False)
        )
        fetch_deleted = (
            session.query(FetchStatus)
            .filter(FetchStatus.profile_id == profile_id)
            .delete(synchronize_session=False)
        )
        session.commit()
        logger.info(
            f"🗑️  Profile '{profile_id}' data cleaned up: "
            f"{logs_deleted} DNS logs, {fetch_deleted} fetch status rows deleted"
        )
        return {
            "dns_logs_deleted": logs_deleted,
            "fetch_status_deleted": fetch_deleted,
        }
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error deleting data for profile '{profile_id}': {e}")
        return {"dns_logs_deleted": 0, "fetch_status_deleted": 0}
    finally:
        session.close()


def delete_profile(profile_id: str, delete_data: bool = True) -> dict:
    """Remove a profile from nextdns_profiles (and optionally its data).

    Args:
        profile_id: The profile to remove.
        delete_data: If True (default), also delete DNS logs and fetch status.

    Returns:
        dict with keys ``deleted`` (bool) and cleanup counts.
    """
    cleanup = {"dns_logs_deleted": 0, "fetch_status_deleted": 0}
    if delete_data:
        cleanup = delete_profile_data(profile_id)

    session = session_factory()
    try:
        deleted = (
            session.query(NextDNSProfile)
            .filter_by(profile_id=profile_id)
            .delete(synchronize_session=False)
        )
        session.commit()
        if deleted:
            logger.info(f"🗑️  Profile '{profile_id}' removed from nextdns_profiles")
            return {"deleted": True, **cleanup}
        logger.warning(f"⚠️  Profile '{profile_id}' not found for deletion")
        return {"deleted": False, **cleanup}
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error deleting profile '{profile_id}': {e}")
        return {"deleted": False, **cleanup}
    finally:
        session.close()


# ---------------------------------------------------------------------------
# One-time startup migration from environment variables
# ---------------------------------------------------------------------------


def migrate_config_from_env() -> bool:
    """Seed system_settings and nextdns_profiles from env vars if both are empty.

    This runs once on first boot after the migration adds the new tables.
    Subsequent boots skip seeding because rows already exist.

    Returns:
        True if seeding was performed, False if tables already had data.
    """
    session = session_factory()
    try:
        has_settings = session.query(SystemSetting).first() is not None
        has_profiles = session.query(NextDNSProfile).first() is not None
    except SQLAlchemyError as e:
        logger.error(f"❌ migrate_config_from_env: cannot query tables: {e}")
        return False
    finally:
        session.close()

    if has_settings and has_profiles:
        logger.debug("🧱 Config tables already populated — skipping env migration")
        return False

    seeded = False

    # Seed API key
    if not has_settings:
        api_key = os.getenv("API_KEY")
        if api_key:
            set_nextdns_api_key(api_key)
            logger.info("🔑 Migrated NextDNS API key from env to system_settings")
            seeded = True
        else:
            logger.warning(
                "⚠️  API_KEY env var not set — NextDNS API key not migrated. "
                "Set it via PUT /settings/nextdns/api-key after startup."
            )

    # Seed profiles
    if not has_profiles:
        env_ids = os.getenv("PROFILE_IDS", "")
        profile_ids = [p.strip() for p in env_ids.split(",") if p.strip()]
        if profile_ids:
            for pid in profile_ids:
                add_profile(pid)
            logger.info(
                f"🧱 Migrated {len(profile_ids)} profile(s) from PROFILE_IDS env to DB"
            )
            seeded = True
        else:
            logger.warning(
                "⚠️  PROFILE_IDS env var not set — no profiles migrated. "
                "Add profiles via POST /settings/nextdns/profiles after startup."
            )

    return seeded
