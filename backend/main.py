# file: backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
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

# Track application start time for accurate uptime
app_start_time = datetime.now(timezone.utc)

# Import models and scheduler
from models import init_db, get_logs, get_total_record_count, get_logs_stats, get_available_profiles
try:
    from scheduler import scheduler
    logger.info("🔄 NextDNS log scheduler started successfully")
except ImportError as e:
    logger.warning(f"⚠️  Could not start scheduler: {e}")
    logger.info("🧱 App will work but won't automatically fetch NextDNS logs")

# Initialize FastAPI app
app = FastAPI(
    title="NextDNS Optimized Analytics API",
    description="""FastAPI backend for NextDNS log analytics with automated data fetching.
    
    ## Authentication
    
    Use one of these methods to authenticate:
    
    1. **Bearer Token**: Add `Authorization: Bearer YOUR_API_KEY` header
    2. **X-API-Key Header**: Add `X-API-Key: YOUR_API_KEY` header
    
    The API key is configured via the `LOCAL_API_KEY` environment variable.
    """,
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
security = HTTPBearer()
LOCAL_API_KEY = os.getenv("LOCAL_API_KEY")

def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Authenticate user with API key."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=401,
            detail="API key required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not secrets.compare_digest(credentials.credentials, LOCAL_API_KEY or ""):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return "authenticated"

# Flexible authentication supporting both Bearer and X-API-Key
def verify_api_key_flexible(
    x_api_key: str = Header(None),
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
):
    """Authenticate user with API key via Bearer token or X-API-Key header."""
    api_key = None
    
    # Try Bearer token first
    if credentials and credentials.credentials:
        api_key = credentials.credentials
    # Fall back to X-API-Key header
    elif x_api_key:
        api_key = x_api_key
    
    if not api_key:
        raise HTTPException(
            status_code=401,
            detail="API key required via Authorization header (Bearer token) or X-API-Key header",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not secrets.compare_digest(api_key, LOCAL_API_KEY or ""):
        raise HTTPException(
            status_code=401,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return "authenticated"

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

class LogsStatsResponse(BaseModel):
    """Response model for logs statistics."""
    total: int
    blocked: int
    allowed: int
    blocked_percentage: float
    allowed_percentage: float
    profile_id: Optional[str] = None

class ProfileInfo(BaseModel):
    """Profile information model."""
    profile_id: str
    record_count: int
    last_activity: Optional[str] = None

class ProfileListResponse(BaseModel):
    """Response model for profile list."""
    profiles: List[ProfileInfo]
    total_profiles: int

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
        current_time = datetime.now(timezone.utc)
        uptime_seconds = (current_time - app_start_time).total_seconds()
        
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
            "cpu_count_logical": psutil.cpu_count(logical=True),
            "frontend_stack": {
                "framework": "React 19.1.1",
                "build_tool": "Vite 7.1.6",
                "language": "TypeScript 5.5.3",
                "styling": "Tailwind CSS 3.4.0",
                "ui_library": "shadcn/ui + Radix UI",
                "state_management": "TanStack Query 5.56.2"
            }
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
async def get_stats():
    """Get database statistics."""
    total_records = get_total_record_count()
    logger.info(f"📊 Stats requested: {total_records:,} total records")
    
    return StatsResponse(
        total_records=total_records,
        message=f"Database contains {total_records:,} DNS log records"
    )

@app.get("/logs/stats", response_model=LogsStatsResponse, tags=["Logs"])
async def get_logs_statistics():
    """Get statistics for all DNS logs in the database."""
    logger.debug("📊 API request for logs statistics")
    stats = get_logs_stats()
    logger.info(f"📊 Returning stats: {stats}")
    return LogsStatsResponse(**stats)

@app.get("/logs", response_model=LogsResponse, tags=["Logs"])
async def get_dns_logs(
    exclude: Optional[List[str]] = Query(default=None, description="Domains to exclude from results"),
    search: Optional[str] = Query(default="", description="Search query for domain names"),
    status: Optional[str] = Query(default="all", description="Filter by status: all, blocked, allowed"),
    profile: Optional[str] = Query(default=None, description="Filter by specific profile ID"),
    limit: int = Query(default=100, ge=1, le=10000, description="Maximum number of records to return"),
    offset: int = Query(default=0, ge=0, description="Number of records to skip")
):
    """
    Get DNS logs with optional filtering and pagination.
    
    - **exclude**: List of domains to exclude from results
    - **search**: Search query for domain names
    - **status**: Filter by status (all, blocked, allowed)
    - **profile**: Filter by specific profile ID
    - **limit**: Maximum number of records to return (1-10000)
    - **offset**: Number of records to skip for pagination
    """
    logger.debug(f"📊 API request: exclude={exclude}, search='{search}', status={status}, profile='{profile}', limit={limit}, offset={offset}")
    
    logs = get_logs(
        exclude_domains=exclude, 
        search_query=search,
        status_filter=status,
        profile_filter=profile,
        limit=limit, 
        offset=offset
    )
    total_records = get_total_record_count()
    
    logger.info(f"📊 Returning {len(logs)} DNS logs")
    
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