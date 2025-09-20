# file: backend/models.py
import json
import os
from datetime import datetime, timezone, timedelta

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
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

# Set up logging
from logging_config import get_logger

logger = get_logger(__name__)


# Custom Text type that forces TEXT without JSON casting
class ForceText(TypeDecorator):  # pylint: disable=too-many-ancestors
    """Custom SQLAlchemy type that forces values to be stored as text."""

    impl = Text
    cache_ok = True  # SQLAlchemy 1.4+ requirement

    def process_bind_param(self, value, dialect):  # pylint: disable=unused-argument
        if value is not None:
            return str(value)
        return value

    def process_result_value(self, value, dialect):  # pylint: disable=unused-argument
        return value

    def process_literal_param(self, value, dialect):  # pylint: disable=unused-argument
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
    f"{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/"
    f"{os.getenv('POSTGRES_DB')}"
)
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)


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
    data = Column(ForceText, nullable=False)  # Store original raw data as JSON string
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


# Get total record count from database
def get_total_record_count():
    """Get the total number of DNS log records in the database.

    Returns:
        int: Total number of records, or 0 if error occurs
    """
    session = Session()
    try:
        count = session.query(DNSLog).count()
        logger.debug(f"📊 Database contains {count:,} total DNS log records")
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
    session = Session()
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
                timestamp=log_timestamp, domain=log.get("domain"), client_ip=client_ip
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

        new_log = DNSLog(
            timestamp=log_timestamp,
            domain=log.get("domain"),
            action=action,
            device=device_str,
            client_ip=client_ip,
            query_type=log.get("query_type", "A"),
            blocked=blocked,
            profile_id=log.get("profile_id"),
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
    session = Session()
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
    session = Session()
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
def get_logs(  # pylint: disable=too-many-positional-arguments
    exclude_domains=None,
    search_query="",
    status_filter="all",
    profile_filter=None,
    limit=100,
    offset=0,
):
    """Retrieve DNS logs with optional filtering and pagination.

    Args:
        exclude_domains (list): List of domains to exclude from results
        search_query (str): Domain name search query
        status_filter (str): Filter by status - 'all', 'blocked', 'allowed'
        profile_filter (str): Filter by specific profile ID
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip for pagination

    Returns:
        list: List of DNS log dictionaries
    """
    total_records = get_total_record_count()
    logger.debug(
        f"📊 Retrieving logs with limit={limit}, offset={offset}, "
        f"exclude_domains={exclude_domains}, search='{search_query}', "
        f"status='{status_filter}', profile='{profile_filter}'"
    )
    logger.info(
        f"📊 Database query: requesting {limit} records from {total_records:,} total records"
    )
    session = Session()
    try:
        query = session.query(DNSLog).order_by(DNSLog.timestamp.desc())

        # Apply domain exclusions
        if exclude_domains:
            query = query.filter(~DNSLog.domain.in_(exclude_domains))
            logger.debug(f"🚫 Excluding {len(exclude_domains)} domains from results")

        # Apply search filter on domain name
        if search_query.strip():
            query = query.filter(DNSLog.domain.ilike(f"%{search_query}%"))
            logger.debug(f"🔍 Filtering by domain search: '{search_query}'")

        # Apply status filter
        if status_filter == "blocked":
            query = query.filter(DNSLog.blocked is True)
            logger.debug("🚫 Filtering for blocked requests only")
        elif status_filter == "allowed":
            query = query.filter(DNSLog.blocked is False)
            logger.debug("✅ Filtering for allowed requests only")

        # Apply profile filter
        if profile_filter and profile_filter.strip():
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Filtering for profile: '{profile_filter}'")

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
        return result
    except SQLAlchemyError as e:
        logger.error(f"❌ Error retrieving logs from database: {e}")
        return []
    finally:
        session.close()


# Get total statistics for all logs in the database
def get_logs_stats(profile_filter=None):
    """Get statistics for DNS logs in the database, optionally filtered by profile.

    Args:
        profile_filter (str): Optional profile ID to filter statistics

    Returns:
        dict: Dictionary containing total, blocked, and allowed counts and percentages
    """
    session = Session()
    try:
        query = session.query(DNSLog)

        # Apply profile filter if specified
        if profile_filter and profile_filter.strip():
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Getting stats for profile: '{profile_filter}'")

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
    session = Session()
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
def get_stats_overview(profile_filter=None, time_range="24h"):
    """Get overview statistics from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by (1h, 24h, 7d, 30d, all)

    Returns:
        dict: Statistics overview
    """
    session = Session()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)
            logger.debug(f"🧱 Filtering stats for profile: '{profile_filter}'")

        # Apply time range filter
        if time_range != "all":

            now = datetime.now(timezone.utc)

            time_deltas = {
                "1h": timedelta(hours=1),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
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
        hours_map = {"1h": 1, "24h": 24, "7d": 168, "30d": 720, "all": 1}
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

        # Get top blocked domain
        top_blocked_domain = None
        try:
            # pylint: disable=not-callable
            blocked_domain_result = (
                session.query(DNSLog.domain, func.count(DNSLog.id).label("count"))
                .filter(DNSLog.blocked.is_(True))
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
def get_stats_timeseries(profile_filter=None, time_range="24h", granularity="hour"):
    """Get time series statistics from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by
        granularity (str): Time granularity (hour, day, etc.)

    Returns:
        list: List of time series data points
    """
    session = Session()
    try:

        now = datetime.now(timezone.utc)

        # Determine time parameters based on time range
        if time_range == "1h":
            start_time = now - timedelta(hours=1)
            interval_minutes = 5
            num_intervals = 12  # 12 x 5min = 1 hour
            granularity = "5min"
        elif time_range == "24h":
            start_time = now - timedelta(hours=24)
            interval_hours = 1
            num_intervals = 24  # 24 x 1hour = 24 hours
            granularity = "hour"
        elif time_range == "7d":
            start_time = now - timedelta(days=7)
            interval_hours = 24
            num_intervals = 7  # 7 x 1day = 7 days
            granularity = "day"
        elif time_range == "30d":
            start_time = now - timedelta(days=30)
            interval_hours = 24
            num_intervals = 30  # 30 x 1day = 30 days
            granularity = "day"
        else:  # 'all'
            # For 'all', we'll use daily intervals for the last 30 days
            start_time = now - timedelta(days=30)
            interval_hours = 24
            num_intervals = 30
            granularity = "day"

        # Build base query
        base_query = session.query(DNSLog).filter(DNSLog.timestamp >= start_time)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            base_query = base_query.filter(DNSLog.profile_id == profile_filter)

        # Generate time buckets
        data_points = []
        for i in range(num_intervals):
            if time_range == "1h":
                interval_start = start_time + timedelta(minutes=i * interval_minutes)
                interval_end = interval_start + timedelta(minutes=interval_minutes)
                # Round to nearest 5 minutes for clean display
                display_time = interval_start.replace(
                    minute=(interval_start.minute // 5) * 5, second=0, microsecond=0
                )
            else:
                interval_start = start_time + timedelta(hours=i * interval_hours)
                interval_end = interval_start + timedelta(hours=interval_hours)
                if granularity == "hour":
                    # Round to exact hour for clean display
                    display_time = interval_start.replace(
                        minute=0, second=0, microsecond=0
                    )
                else:  # day
                    # Round to start of day for clean display
                    display_time = interval_start.replace(
                        hour=0, minute=0, second=0, microsecond=0
                    )

            # Query for this interval
            interval_query = base_query.filter(
                DNSLog.timestamp >= interval_start, DNSLog.timestamp < interval_end
            )

            total_queries = interval_query.count()
            blocked_queries = interval_query.filter(DNSLog.blocked.is_(True)).count()
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
        return data_points

    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting time series data: {e}")
        return []
    finally:
        session.close()


# Get top domains from database
def get_top_domains(profile_filter=None, time_range="24h", limit=10):
    """Get top blocked and allowed domains from the database.

    Args:
        profile_filter (str): Optional profile ID to filter by
        time_range (str): Time range to filter by
        limit (int): Number of top domains to return

    Returns:
        dict: Contains blocked_domains and allowed_domains lists
    """
    session = Session()
    try:
        # Build base query
        query = session.query(DNSLog)

        # Apply profile filter
        if profile_filter and profile_filter.strip() and profile_filter != "all":
            query = query.filter(DNSLog.profile_id == profile_filter)

        # Apply time range filter
        if time_range != "all":

            now = datetime.now(timezone.utc)

            time_deltas = {
                "1h": timedelta(hours=1),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
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
                    session.query(DNSLog.domain, func.count(DNSLog.id).label("count"))
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
                    session.query(DNSLog.domain, func.count(DNSLog.id).label("count"))
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
