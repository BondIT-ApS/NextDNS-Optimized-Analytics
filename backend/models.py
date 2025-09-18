# file: backend/models.py
from sqlalchemy import create_engine, Column, Integer, String, Text, JSON, DateTime, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import os

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
    action = Column(String(50), nullable=False)  # allowed, blocked, etc.
    device = Column(String(255), nullable=False)
    client_ip = Column(String(45))  # Support IPv4 and IPv6
    query_type = Column(String(10), default='A')  # A, AAAA, CNAME, etc.
    blocked = Column(Boolean, default=False, nullable=False, index=True)
    profile_id = Column(String(50), index=True)
    data = Column(JSON, nullable=False)  # Store original raw data
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Add composite indexes for common queries
    __table_args__ = (
        Index('idx_dns_logs_timestamp_domain', 'timestamp', 'domain'),
        Index('idx_dns_logs_domain_action', 'domain', 'action'),
        Index('idx_dns_logs_profile_timestamp', 'profile_id', 'timestamp'),
    )

# Initialize the database (now handled by Alembic migrations)
def init_db():
    # Note: Database initialization is now handled by Alembic migrations
    # Run 'alembic upgrade head' to initialize/update the database schema
    print("Database initialization is handled by Alembic migrations.")
    print("Run 'alembic upgrade head' to ensure database schema is up to date.")

# Add log entry to the database
def add_log(log):
    """Add a DNS log entry to the database.
    
    Args:
        log (dict): DNS log data containing domain, action, device, and other fields
    """
    session = Session()
    try:
        new_log = DNSLog(
            domain=log.get("domain"),
            action=log.get("action"),
            device=log.get("device"),
            client_ip=log.get("client_ip"),
            query_type=log.get("query_type", "A"),
            blocked=log.get("blocked", log.get("action") == "blocked"),
            profile_id=log.get("profile_id"),
            data=log  # Store the complete original log
        )
        session.add(new_log)
        session.commit()
        return new_log.id
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error adding log: {e}")
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
    session = Session()
    try:
        query = session.query(DNSLog).order_by(DNSLog.timestamp.desc())
        
        if exclude_domains:
            query = query.filter(~DNSLog.domain.in_(exclude_domains))
        
        # Apply pagination
        query = query.offset(offset).limit(limit)
        
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "domain": log.domain,
                "action": log.action,
                "device": log.device,
                "client_ip": log.client_ip,
                "query_type": log.query_type,
                "blocked": log.blocked,
                "profile_id": log.profile_id,
                "data": log.data,
                "created_at": log.created_at.isoformat(),
            }
            for log in query.all()
        ]
    except SQLAlchemyError as e:
        print(f"Error retrieving logs: {e}")
        return []
    finally:
        session.close()
