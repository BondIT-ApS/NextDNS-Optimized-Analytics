from sqlalchemy import create_engine, Column, Integer, Text, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
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
    timestamp = Column(DateTime, default=datetime.utcnow)
    domain = Column(Text, nullable=False)
    action = Column(Text, nullable=False)
    device = Column(Text, nullable=False)
    data = Column(JSON, nullable=False)

# Initialize the database
def init_db():
    try:
        Base.metadata.create_all(engine)
        print("Database initialized successfully.")
    except SQLAlchemyError as e:
        print(f"Error initializing database: {e}")

# Add log entry to the database
def add_log(log):
    session = Session()
    try:
        new_log = DNSLog(
            domain=log.get("domain"),
            action=log.get("action"),
            device=log.get("device"),
            data=log
        )
        session.add(new_log)
        session.commit()
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Error adding log: {e}")
    finally:
        session.close()

# Retrieve logs with optional exclusion of domains
def get_logs(exclude_domains=None):
    session = Session()
    try:
        query = session.query(DNSLog)
        if exclude_domains:
            query = query.filter(~DNSLog.domain.in_(exclude_domains))
        return [
            {
                "id": log.id,
                "timestamp": log.timestamp.isoformat(),
                "domain": log.domain,
                "action": log.action,
                "device": log.device,
                "data": log.data,
            }
            for log in query.all()
        ]
    except SQLAlchemyError as e:
        print(f"Error retrieving logs: {e}")
        return []
    finally:
        session.close()
