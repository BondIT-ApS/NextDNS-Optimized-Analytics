# file: backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index, TypeDecorator, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import os
import json

# Set up logging
from logging_config import get_logger
logger = get_logger(__name__)

# Custom Text type that forces TEXT without JSON casting
class ForceText(TypeDecorator):
    impl = Text
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        return value

# Base declaration
Base = declarative_base()

# Database connection setup
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"
engine = create_engine(DATABASE_URL, echo=False)
Session = sessionmaker(bind=engine)

# Database model for DNS logs
class DNSLog(Base):
    __tablename__ = "dns_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    domain = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=True, default='default')  # allowed, blocked, etc.
    device = Column(ForceText, nullable=True)  # Store device info as JSON string
    client_ip = Column(String(45))  # Support IPv4 and IPv6
    query_type = Column(String(10), default='A')  # A, AAAA, CNAME, etc.
    blocked = Column(Boolean, default=False, nullable=False, index=True)
    profile_id = Column(String(50), index=True)
    data = Column(ForceText, nullable=False)  # Store original raw data as JSON string
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Add composite indexes and unique constraint for duplicate prevention
    __table_args__ = (
        Index('idx_dns_logs_timestamp_domain', 'timestamp', 'domain'),
        Index('idx_dns_logs_domain_action', 'domain', 'action'),
        Index('idx_dns_logs_profile_timestamp', 'profile_id', 'timestamp'),
        # Unique constraint to prevent duplicates based on timestamp, domain, and client_ip
        UniqueConstraint('timestamp', 'domain', 'client_ip', name='uq_dns_logs_timestamp_domain_client'),
    )

# Database model for tracking fetch progress
class FetchStatus(Base):
    __tablename__ = "fetch_status"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    last_fetch_timestamp = Column(DateTime(timezone=True), nullable=False)
    last_successful_fetch = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    records_fetched = Column(Integer, default=0, nullable=False)
    profile_id = Column(String(50), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    __table_args__ = (
        # Ensure we only have one status record per profile
        UniqueConstraint('profile_id', name='uq_fetch_status_profile'),
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
    logger.info("🔄 Run 'alembic upgrade head' to ensure database schema is up to date.")
    
    # Log current database status
    total_records = get_total_record_count()
    logger.info(f"💾 Database currently contains {total_records:,} DNS log records")

# Add log entry to the database with duplicate prevention
def add_log(log):
    """Add a DNS log entry to the database with duplicate prevention.
    
    Args:
        log (dict): DNS log data containing domain, action, device, and other fields
        
    Returns:
        tuple: (record_id, is_new) where record_id is the ID and is_new indicates if it's a new record
    """
    session = Session()
    try:
        # Extract timestamp from log data
        log_timestamp_str = log.get("timestamp")
        if log_timestamp_str:
            # Parse NextDNS timestamp format: 2025-09-18T08:11:39.673Z
            log_timestamp = datetime.fromisoformat(log_timestamp_str.replace('Z', '+00:00'))
        else:
            log_timestamp = datetime.now(timezone.utc)
        
        # Determine action based on NextDNS log structure
        action = log.get("action") or log.get("status") or "default"
        
        # Handle device - extract name if it's a dict, otherwise use as is
        device_info = log.get("device")
        
        # Handle client info - could be in clientIp field
        client_ip = log.get("client_ip") or log.get("clientIp")
        
        # Check for existing record first (duplicate prevention)
        existing_log = session.query(DNSLog).filter_by(
            timestamp=log_timestamp,
            domain=log.get("domain"),
            client_ip=client_ip
        ).first()
        
        if existing_log:
            logger.debug(f"🔄 Duplicate found for domain {log.get('domain')} at {log_timestamp} - skipping")
            return existing_log.id, False  # Return existing ID, not new
        
        # Determine if request was blocked
        blocked = (
            log.get("blocked", False) or
            action == "blocked" or
            log.get("status") == "blocked"
        )

        # Ensure all JSON data is properly serialized as strings
        device_str = json.dumps(device_info) if device_info else None
        data_str = json.dumps(log) if isinstance(log, dict) else str(log)
        
        # Debug output to check data types (only in DEBUG mode)
        logger.debug(f"🐛 Data serialization - device type: {type(device_str)}, device value: {device_str}")
        logger.debug(f"🐛 Data serialization - data type: {type(data_str)}, data value (first 100 chars): {str(data_str)[:100]}")

        new_log = DNSLog(
            timestamp=log_timestamp,
            domain=log.get("domain"),
            action=action,
            device=device_str,
            client_ip=client_ip,
            query_type=log.get("query_type", "A"),
            blocked=blocked,
            profile_id=log.get("profile_id"),
            data=data_str
        )
        session.add(new_log)
        session.commit()
        logger.debug(f"💾 Successfully added NEW log for domain: {log.get('domain')} at {log_timestamp}")
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
        fetch_status = session.query(FetchStatus).filter_by(profile_id=profile_id).first()
        if fetch_status:
            logger.debug(f"📅 Last fetch for profile {profile_id}: {fetch_status.last_fetch_timestamp}")
            return fetch_status.last_fetch_timestamp
        else:
            logger.debug(f"📅 No previous fetch found for profile {profile_id}")
            return None
    except SQLAlchemyError as e:
        logger.error(f"❌ Error getting last fetch timestamp: {e}")
        return None
    finally:
        session.close()

# Update fetch status after successful fetch
def update_fetch_status(profile_id, last_timestamp, records_count):
    """Update or create fetch status record.
    
    Args:
        profile_id (str): NextDNS profile ID
        last_timestamp (datetime): Timestamp of the last fetched record
        records_count (int): Number of records fetched in this batch
    """
    session = Session()
    try:
        fetch_status = session.query(FetchStatus).filter_by(profile_id=profile_id).first()
        
        if fetch_status:
            # Update existing record
            fetch_status.last_fetch_timestamp = last_timestamp
            fetch_status.last_successful_fetch = datetime.now(timezone.utc)
            fetch_status.records_fetched += records_count
            fetch_status.updated_at = datetime.now(timezone.utc)
            logger.debug(f"📅 Updated fetch status for profile {profile_id}: last_timestamp={last_timestamp}, total_records={fetch_status.records_fetched}")
        else:
            # Create new record
            fetch_status = FetchStatus(
                profile_id=profile_id,
                last_fetch_timestamp=last_timestamp,
                records_fetched=records_count
            )
            session.add(fetch_status)
            logger.debug(f"📅 Created new fetch status for profile {profile_id}: last_timestamp={last_timestamp}, records={records_count}")
        
        session.commit()
        return True
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error updating fetch status: {e}")
        return False
    finally:
        session.close()

# Retrieve logs with optional exclusion of domains
def get_logs(exclude_domains=None, limit=1000, offset=0):
    """Retrieve DNS logs with optional filtering and pagination.
    
    Args:
        exclude_domains (list): List of domains to exclude from results
        limit (int): Maximum number of records to return
        offset (int): Number of records to skip for pagination
    
    Returns:
        list: List of DNS log dictionaries
    """
    total_records = get_total_record_count()
    logger.debug(f"📊 Retrieving logs with limit={limit}, offset={offset}, exclude_domains={exclude_domains}")
    logger.info(f"📊 Database query: requesting {limit} records from {total_records:,} total records")
    session = Session()
    try:
        query = session.query(DNSLog).order_by(DNSLog.timestamp.desc())
        
        if exclude_domains:
            query = query.filter(~DNSLog.domain.in_(exclude_domains))
            logger.debug(f"🚫 Excluding {len(exclude_domains)} domains from results")
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "domain": log.domain,
                "action": log.action,
                "device": json.loads(log.device) if log.device else None,
                "client_ip": log.client_ip,
                "query_type": log.query_type,
                "blocked": log.blocked,
                "profile_id": log.profile_id,
                "data": json.loads(log.data) if log.data else None,
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
