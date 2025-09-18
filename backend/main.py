# file: backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import secrets
import psutil
import platform
from datetime import datetime, timezone

# Set up logging first
from logging_config import setup_logging, get_logger
setup_logging()
logger = get_logger(__name__)

# Import models and scheduler
from models import init_db, get_logs, get_total_record_count
try:
    from scheduler import scheduler
    logger.info("🔄 NextDNS log scheduler started successfully")
except ImportError as e:
    logger.warning(f"⚠️  Could not start scheduler: {e}")
    logger.info("🧱 App will work but won't automatically fetch NextDNS logs")

# Initialize FastAPI app
app = FastAPI(
    title="NextDNS Optimized Analytics API",
    description="FastAPI backend for NextDNS log analytics with automated data fetching",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication setup
security = HTTPBasic()
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY")

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    """Authenticate user with basic auth."""
    correct_username = secrets.compare_digest(credentials.username, "admin")
    correct_password = secrets.compare_digest(credentials.password, LOCAL_API_KEY)
    
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

# Pydantic models for request/response
from pydantic import BaseModel
from typing import Dict, Any

class DNSLogResponse(BaseModel):
    """DNS log response model."""
    id: int
    timestamp: str
    domain: str
    action: str
    device: Optional[Dict[str, Any]] = None
    client_ip: Optional[str] = None
    query_type: str = "A"
    blocked: bool = False
    profile_id: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    created_at: str

class LogsResponse(BaseModel):
    """Response model for logs endpoint."""
    data: List[DNSLogResponse]
    total_records: int
    returned_records: int
    excluded_domains: Optional[List[str]] = None

class StatsResponse(BaseModel):
    """Response model for statistics."""
    total_records: int
    message: str

class HealthResponse(BaseModel):
    """Simple health response model."""
    status: str
    healthy: bool

class SystemResources(BaseModel):
    """System resource information."""
    cpu_percent: float
    memory_total: int
    memory_available: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    uptime_seconds: float

class DetailedHealthResponse(BaseModel):
    """Detailed health response model."""
    status_api: str
    status_db: str
    healthy: bool
    total_dns_records: int
    fetch_interval_minutes: int
    log_level: str
    system_resources: SystemResources
    server_info: Dict[str, Any]
    timestamp: str

# API Endpoints

@app.on_event("startup")
async def startup_event():
    """Initialize the application on startup."""
    logger.info("🚀 Starting NextDNS Optimized Analytics FastAPI Backend")
    init_db()  # Ensure the database is initialized
    logger.info("✅ FastAPI application startup completed")

@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check."""
    total_records = get_total_record_count()
    return {
        "message": "NextDNS Optimized Analytics API",
        "version": "2.0.0",
        "status": "running",
        "total_dns_records": total_records
    }

@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    try:
        # Quick database check
        total_records = get_total_record_count()
        db_healthy = total_records >= 0
        
        return HealthResponse(
            status="healthy" if db_healthy else "unhealthy",
            healthy=db_healthy
        )
    except Exception as e:
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            healthy=False
        )

@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """Detailed health check with comprehensive system information."""
    try:
        # Database check
        total_records = get_total_record_count()
        db_healthy = total_records >= 0
        
        # System resource monitoring
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        boot_time = psutil.boot_time()
        current_time = datetime.now(timezone.utc).timestamp()
        uptime_seconds = current_time - boot_time
        
        # Get environment variables
        fetch_interval = int(os.getenv("FETCH_INTERVAL", 60))
        log_level = os.getenv("LOG_LEVEL", "INFO")
        
        system_resources = SystemResources(
            cpu_percent=cpu_percent,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_percent=memory.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_percent=(disk.used / disk.total) * 100,
            uptime_seconds=uptime_seconds
        )
        
        server_info = {
            "platform": platform.system(),
            "platform_release": platform.release(),
            "architecture": platform.machine(),
            "hostname": platform.node(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_count_logical": psutil.cpu_count(logical=True)
        }
        
        api_healthy = True  # API is responding if we get here
        overall_healthy = db_healthy and api_healthy
        
        logger.debug(f"🏥 Detailed health check completed - Overall: {overall_healthy}, DB: {db_healthy}, API: {api_healthy}")
        
        return DetailedHealthResponse(
            status_api="healthy" if api_healthy else "unhealthy",
            status_db="healthy" if db_healthy else "unhealthy",
            healthy=overall_healthy,
            total_dns_records=total_records,
            fetch_interval_minutes=fetch_interval,
            log_level=log_level,
            system_resources=system_resources,
            server_info=server_info,
            timestamp=datetime.now(timezone.utc).isoformat()
        )
        
    except Exception as e:
        logger.error(f"❌ Detailed health check failed: {e}")
        # Return minimal error response
        return DetailedHealthResponse(
            status_api="unhealthy",
            status_db="unknown",
            healthy=False,
            total_dns_records=0,
            fetch_interval_minutes=60,
            log_level="UNKNOWN",
            system_resources=SystemResources(
                cpu_percent=0.0,
                memory_total=0,
                memory_available=0,
                memory_percent=0.0,
                disk_total=0,
                disk_used=0,
                disk_percent=0.0,
                uptime_seconds=0.0
            ),
            server_info={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat()
        )

@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(current_user: str = Depends(get_current_user)):
    """Get database statistics."""
    total_records = get_total_record_count()
    logger.info(f"📊 Stats requested by {current_user}: {total_records:,} total records")
    
    return StatsResponse(
        total_records=total_records,
        message=f"Database contains {total_records:,} DNS log records"
    )

@app.get("/logs", response_model=LogsResponse, tags=["Logs"])
async def get_dns_logs(
    exclude: Optional[List[str]] = Query(default=None, description="Domains to exclude from results"),
    limit: int = Query(default=1000, ge=1, le=10000, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: str = Depends(get_current_user)
):
    """
    Get DNS logs with optional filtering and pagination.
    
    - **exclude**: List of domains to exclude from results
    - **limit**: Maximum number of records to return (1-10000)
    - **offset**: Number of records to skip for pagination
    """
    logger.debug(f"📊 API request from {current_user}: exclude={exclude}, limit={limit}, offset={offset}")
    
    logs = get_logs(exclude_domains=exclude, limit=limit, offset=offset)
    total_records = get_total_record_count()
    
    logger.info(f"📊 Returning {len(logs)} DNS logs to {current_user}")
    
    return LogsResponse(
        data=logs,
        total_records=total_records,
        returned_records=len(logs),
        excluded_domains=exclude
    )

if __name__ == "__main__":
    import uvicorn
    logger.info("🖥️  Starting FastAPI server with uvicorn on 0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")