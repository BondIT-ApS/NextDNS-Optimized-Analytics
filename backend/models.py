# file: backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, Index, TypeDecorator
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

# Database model
class DNSLog(Base):
    __tablename__ = "dns_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    domain = Column(String(255), nullable=False, index=True)
    action = Column(String(50), nullable=True, default='default')  # allowed, blocked, etc.
    device = Column(ForceText, nullable=True)  # Store device info as JSON string
    client_ip = Column(String(45))  # Support IPv4 and IPv6
    query_type = Column(String(10), default='A')  # A, AAAA, CNAME, etc.
    blocked = Column(Boolean, default=False, nullable=False, index=True)
    profile_id = Column(String(50), index=True)
    data = Column(ForceText, nullable=False)  # Store original raw data as JSON string
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_dns_logs_timestamp_domain', 'timestamp', 'domain'),
        Index('idx_dns_logs_domain_action', 'domain', 'action'),
        Index('idx_dns_logs_profile_timestamp', 'profile_id', 'timestamp'),
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

# Add log entry to the database
def add_log(log):
    """Add a DNS log entry to the database.
    
    Args:
        log (dict): DNS log data containing domain, action, device, and other fields
    """
    session = Session()
    try:
        # Determine action based on NextDNS log structure
        action = log.get("action") or log.get("status") or "default"
        
        # Handle device - extract name if it's a dict, otherwise use as is
        device_info = log.get("device")
        
        # Handle client info - could be in clientIp field
        client_ip = log.get("client_ip") or log.get("clientIp")
        
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
        logger.debug(f"💾 Successfully added log for domain: {log.get('domain')}")
        return new_log.id
    except SQLAlchemyError as e:
        session.rollback()
        logger.error(f"❌ Error adding log to database: {e}")
        return None
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
