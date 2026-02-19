# file: backend/main.py
import os
import platform
import secrets
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import psutil
from fastapi import FastAPI, Depends, HTTPException, Query, Header, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.exc import SQLAlchemyError

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Set up logging first
from logging_config import setup_logging, get_logger, apply_log_level
from performance_middleware import PerformanceMiddleware
from auth import (
    init_auth,
    authenticate_user,
    create_access_token,
    get_current_user,
    LoginRequest,
    LoginResponse,
    AuthStatus,
    AuthConfig,
    AUTH_ENABLED,
    AUTH_SESSION_TIMEOUT,
)
from models import (
    init_db,
    get_logs,
    get_total_record_count,
    get_logs_stats,
    check_database_health,
    get_nextdns_api_key,
    set_nextdns_api_key,
    get_all_profiles,
    get_profile,
    add_profile,
    update_profile_enabled,
    delete_profile,
    migrate_config_from_env,
    get_fetch_interval,
    set_fetch_interval,
    get_fetch_limit,
    set_fetch_limit,
    get_log_level,
    set_log_level,
)
from models import get_available_profiles as get_profiles_from_db
from models import (
    get_stats_overview as get_db_stats_overview,
    get_stats_timeseries as get_db_stats_timeseries,
    get_top_domains as get_db_top_domains,
    get_stats_tlds,
    get_stats_devices,
    get_database_metrics,
)
from profile_service import (
    get_profile_info,
    get_multiple_profiles_info,
    get_configured_profile_ids,
)

setup_logging()
logger = get_logger(__name__)

# Initialize rate limiter for brute force protection
limiter = Limiter(key_func=get_remote_address)

# Track application start time for accurate uptime
app_start_time = datetime.now(timezone.utc)

# Version from Docker build arg / environment variable
APP_VERSION = os.getenv("APP_VERSION", "dev")

# Scheduler initialization (can be disabled for K8s multi-pod deployments)
# Default: enabled (backward compatible with Docker Compose and single-pod deployments)
DISABLE_SCHEDULER = os.getenv("DISABLE_SCHEDULER", "false").lower() == "true"

apscheduler_instance = None  # Holds the APScheduler instance when running
if not DISABLE_SCHEDULER:
    try:
        from scheduler import (  # pylint: disable=unused-import,duplicate-code
            scheduler as _scheduler_module_scheduler,
        )

        apscheduler_instance = _scheduler_module_scheduler
        logger.info("🔄 NextDNS log scheduler started successfully")
    except ImportError as e:
        logger.warning(f"⚠️  Could not start scheduler: {e}")
        logger.info("🧱 App will work but won't automatically fetch NextDNS logs")
else:
    logger.info("🔇 Scheduler disabled (DISABLE_SCHEDULER=true)")
    logger.info(
        "💡 Use separate worker pod for DNS log fetching in K8s multi-pod setup"
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for application startup and shutdown."""
    # Startup
    logger.info("🚀 Starting NextDNS Optimized Analytics FastAPI Backend")
    init_db()  # Ensure the database is initialized
    init_auth()  # Initialize authentication system
    if migrate_config_from_env():
        logger.info("🔑 NextDNS config seeded from environment variables")
    logger.info("✅ FastAPI application startup completed")
    yield
    # Shutdown (if needed in the future)
    logger.info("👋 FastAPI application shutting down")


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
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add rate limiter state and exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add CORS middleware
# SECURITY: Get allowed origins from environment variable (comma-separated)
# Default includes common development ports
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:5002,http://localhost:5173,http://localhost:3000",
).split(",")

logger.info(f"🔒 CORS configured for origins: {', '.join(ALLOWED_ORIGINS)}")
logger.warning(
    "⚠️  SECURITY: Ensure ALLOWED_ORIGINS is properly configured for production"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,  # Specific origins only - never use ["*"]
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
    expose_headers=["X-Response-Time"],
)

# Add performance monitoring middleware (only in DEBUG mode)
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
if LOG_LEVEL == "DEBUG":
    app.add_middleware(PerformanceMiddleware)
    logger.info("🧱 Performance monitoring middleware enabled (LOG_LEVEL=DEBUG)")
else:
    logger.info(
        "🔇 Performance monitoring middleware disabled (enable with LOG_LEVEL=DEBUG)"
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
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
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


class NextDNSProfileInfo(BaseModel):
    """NextDNS profile detailed information."""

    id: str
    name: str
    fingerprint: Optional[str] = None
    created: Optional[str] = None
    updated: Optional[str] = None
    error: Optional[str] = None


class TimeSeriesDataPoint(BaseModel):
    """Time series data point for charts."""

    timestamp: str
    total_queries: int
    # Legacy fields for status grouping (blocked/allowed)
    blocked_queries: Optional[int] = None
    allowed_queries: Optional[int] = None
    # New field for profile grouping
    profiles: Optional[Dict[str, int]] = None


class TimeSeriesResponse(BaseModel):
    """Response model for time series data."""

    data: List[TimeSeriesDataPoint]
    granularity: str
    total_points: int
    # Available profiles when group_by="profile"
    available_profiles: Optional[List[str]] = None


class TopDomainsItem(BaseModel):
    """Top domain item."""

    domain: str
    count: int
    percentage: float


class TopDomainsResponse(BaseModel):
    """Response model for top domains."""

    blocked_domains: List[TopDomainsItem]
    allowed_domains: List[TopDomainsItem]


class TopTLDsResponse(BaseModel):
    """Response model for top-level domain statistics."""

    blocked_tlds: List[TopDomainsItem]
    allowed_tlds: List[TopDomainsItem]


class DeviceUsageItem(BaseModel):
    """Device usage statistics item."""

    device_name: str
    total_queries: int
    blocked_queries: int
    allowed_queries: int
    blocked_percentage: float
    allowed_percentage: float
    last_activity: str


class DeviceStatsResponse(BaseModel):
    """Response model for device usage statistics."""

    devices: List[DeviceUsageItem]


class StatsOverviewResponse(BaseModel):
    """Response model for stats overview."""

    total_queries: int
    blocked_queries: int
    allowed_queries: int
    blocked_percentage: float
    queries_per_hour: float
    most_active_device: Optional[str] = None
    top_blocked_domain: Optional[str] = None


class ProfileInfoResponse(BaseModel):
    """Response model for profile information."""

    profiles: Dict[str, NextDNSProfileInfo]
    total_profiles: int


class HealthResponse(BaseModel):
    """Simple health response model."""

    status: str
    healthy: bool


class BackendResources(BaseModel):
    """Backend container system resource information."""

    cpu_percent: float
    memory_total: int
    memory_available: int
    memory_percent: float
    disk_total: int
    disk_used: int
    disk_percent: float
    uptime_seconds: float


class BackendStack(BaseModel):
    """Backend technology stack information."""

    platform: str
    platform_release: str
    architecture: str
    hostname: str
    python_version: str
    cpu_count: int
    cpu_count_logical: int


class FrontendStack(BaseModel):
    """Frontend technology stack information."""

    framework: str
    build_tool: str
    language: str
    styling: str
    ui_library: str
    state_management: str


class BackendHealth(BaseModel):
    """Backend health status."""

    status: str
    uptime_seconds: float


class BackendMetrics(BaseModel):
    """Complete backend metrics information."""

    resources: BackendResources
    health: BackendHealth


class ConnectionStats(BaseModel):
    """Database connection statistics."""

    active: int
    total: int
    max_connections: Optional[int] = None
    usage_percent: float


class PerformanceMetrics(BaseModel):
    """Database performance metrics."""

    cache_hit_ratio: float
    database_size_mb: float
    total_queries: int


class DatabaseHealth(BaseModel):
    """Database health status."""

    status: str
    uptime_seconds: int


class DatabaseMetrics(BaseModel):
    """Complete database metrics information."""

    connections: ConnectionStats
    performance: PerformanceMetrics
    health: DatabaseHealth


class DetailedHealthResponse(BaseModel):
    """Detailed health response model."""

    status_api: str
    status_db: str
    healthy: bool
    total_dns_records: int
    fetch_interval_minutes: int
    log_level: str
    backend_metrics: BackendMetrics
    backend_stack: BackendStack
    database_metrics: Optional[DatabaseMetrics] = None
    frontend_stack: FrontendStack
    timestamp: str


# API Endpoints


@app.get("/", tags=["Health"])
async def root():
    """Root endpoint for health check."""
    try:
        check_database_health()
        return {
            "message": "NextDNS Optimized Analytics API",
            "version": APP_VERSION,
            "status": "running",
        }
    except (SQLAlchemyError, ValueError, TypeError) as e:
        logger.error(f"❌ Root health check failed - database offline: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "message": "NextDNS Optimized Analytics API",
                "version": APP_VERSION,
                "status": "unhealthy",
                "error": "Database is offline or unreachable",
            },
        ) from e


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    try:
        # Quick database connectivity check
        check_database_health()
        return HealthResponse(status="healthy", healthy=True)
    except (SQLAlchemyError, ValueError, TypeError) as e:
        logger.error(f"❌ Health check failed - database offline: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "unhealthy", "healthy": False},
        ) from e


def _create_backend_resources(uptime_seconds: float) -> BackendResources:
    """Create backend resource metrics."""
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")

    return BackendResources(
        cpu_percent=cpu_percent,
        memory_total=memory.total,
        memory_available=memory.available,
        memory_percent=memory.percent,
        disk_total=disk.total,
        disk_used=disk.used,
        disk_percent=(disk.used / disk.total) * 100,
        uptime_seconds=uptime_seconds,
    )


def _create_backend_stack() -> BackendStack:
    """Create backend stack information."""
    return BackendStack(
        platform=platform.system(),
        platform_release=platform.release(),
        architecture=platform.machine(),
        hostname=platform.node(),
        python_version=platform.python_version(),
        cpu_count=psutil.cpu_count(),
        cpu_count_logical=psutil.cpu_count(logical=True),
    )


def _create_frontend_stack() -> FrontendStack:
    """Create frontend stack information."""
    return FrontendStack(
        framework="React 19.1.1",
        build_tool="Vite 7.1.6",
        language="TypeScript 5.5.3",
        styling="Tailwind CSS 3.4.0",
        ui_library="shadcn/ui + Radix UI",
        state_management="TanStack Query 5.56.2",
    )


def _get_database_metrics() -> Optional[DatabaseMetrics]:
    """Get database metrics, returning None on error."""
    try:
        db_metrics_data = get_database_metrics()
        logger.debug("📊 Database metrics successfully collected")
        return DatabaseMetrics(
            connections=ConnectionStats(**db_metrics_data["connections"]),
            performance=PerformanceMetrics(**db_metrics_data["performance"]),
            health=DatabaseHealth(**db_metrics_data["health"]),
        )
    except (SQLAlchemyError, ValueError, TypeError, KeyError) as e:
        logger.warning(f"⚠️ Could not collect database metrics: {e}")
        return None


@app.get("/health/detailed", response_model=DetailedHealthResponse, tags=["Health"])
async def detailed_health_check():
    """Detailed health check with comprehensive system information."""
    try:
        # Database connectivity check (lightweight SELECT 1)
        check_database_health()
        db_healthy = True  # If we get here, database is accessible
        api_healthy = True  # API is responding if we get here
        overall_healthy = db_healthy and api_healthy

        # Get estimated record count (uses pg_class, no table scan)
        total_records = get_total_record_count()

        # Calculate uptime
        uptime_seconds = (datetime.now(timezone.utc) - app_start_time).total_seconds()

        # Get environment configuration
        fetch_interval = int(os.getenv("FETCH_INTERVAL", "60"))
        log_level = os.getenv("LOG_LEVEL", "INFO")

        # Create metrics components
        backend_resources = _create_backend_resources(uptime_seconds)
        backend_health = BackendHealth(status="healthy", uptime_seconds=uptime_seconds)
        backend_metrics = BackendMetrics(
            resources=backend_resources, health=backend_health
        )
        backend_stack = _create_backend_stack()
        frontend_stack = _create_frontend_stack()
        database_metrics = _get_database_metrics()

        logger.debug(
            f"🏥 Detailed health check completed - "
            f"Overall: {overall_healthy}, DB: {db_healthy}, API: {api_healthy}"
        )

        return DetailedHealthResponse(
            status_api="healthy" if api_healthy else "unhealthy",
            status_db="healthy" if db_healthy else "unhealthy",
            healthy=overall_healthy,
            total_dns_records=total_records,
            fetch_interval_minutes=fetch_interval,
            log_level=log_level,
            backend_metrics=backend_metrics,
            backend_stack=backend_stack,
            database_metrics=database_metrics,
            frontend_stack=frontend_stack,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except (SQLAlchemyError, ValueError, TypeError, KeyError, OSError) as e:
        logger.error(f"❌ Detailed health check failed - database offline: {e}")
        # Return minimal error response with 503 status
        error_backend_metrics = BackendMetrics(
            resources=BackendResources(
                cpu_percent=0.0,
                memory_total=0,
                memory_available=0,
                memory_percent=0.0,
                disk_total=0,
                disk_used=0,
                disk_percent=0.0,
                uptime_seconds=0.0,
            ),
            health=BackendHealth(status="error", uptime_seconds=0.0),
        )

        error_backend_stack = BackendStack(
            platform="unknown",
            platform_release="unknown",
            architecture="unknown",
            hostname="unknown",
            python_version="unknown",
            cpu_count=0,
            cpu_count_logical=0,
        )

        error_frontend_stack = FrontendStack(
            framework="unknown",
            build_tool="unknown",
            language="unknown",
            styling="unknown",
            ui_library="unknown",
            state_management="unknown",
        )

        error_response = DetailedHealthResponse(
            status_api="unhealthy",
            status_db="unknown",
            healthy=False,
            total_dns_records=0,
            fetch_interval_minutes=60,
            log_level="UNKNOWN",
            backend_metrics=error_backend_metrics,
            backend_stack=error_backend_stack,
            database_metrics=None,
            frontend_stack=error_frontend_stack,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=error_response.model_dump(),
        ) from e


# Authentication Endpoints


@app.get("/auth/config", response_model=AuthConfig, tags=["Authentication"])
async def get_auth_config():
    """Get authentication configuration (whether auth is enabled)."""
    return AuthConfig(
        enabled=AUTH_ENABLED,
        session_timeout_minutes=AUTH_SESSION_TIMEOUT,
    )


@app.post("/auth/login", response_model=LoginResponse, tags=["Authentication"])
@limiter.limit("5/minute")
async def login(request: Request, login_data: LoginRequest):
    """Login with username and password. Rate limited to 5 attempts per minute."""
    if not AUTH_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is disabled",
        )

    if not authenticate_user(login_data.username, login_data.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create access token
    access_token = create_access_token(data={"sub": login_data.username})

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=AUTH_SESSION_TIMEOUT * 60,  # Convert minutes to seconds
    )


@app.post("/auth/logout", tags=["Authentication"])
async def logout():
    """Logout endpoint. Client should remove token."""
    return {"message": "Logged out successfully"}


@app.get("/auth/status", response_model=AuthStatus, tags=["Authentication"])
async def get_auth_status(current_user: str = Depends(get_current_user)):
    """Check authentication status."""
    if not AUTH_ENABLED:
        return AuthStatus(authenticated=False, username=None)

    return AuthStatus(authenticated=True, username=current_user)


@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats(current_user: str = Depends(get_current_user)):
    """Get database statistics."""
    total_records = get_total_record_count()
    logger.info(f"📊 Stats requested: {total_records:,} total records")

    return StatsResponse(
        total_records=total_records,
        message=f"Database contains {total_records:,} DNS log records",
    )


@app.get("/logs/stats", response_model=LogsStatsResponse, tags=["Logs"])
async def get_logs_statistics(
    profile: Optional[str] = Query(
        default=None, description="Filter statistics by specific profile ID"
    ),
    time_range: str = Query(
        default="all", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from statistics (supports wildcards: *.apple.com, tracking.*)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get statistics for DNS logs in the database, optionally filtered by profile and time range."""
    logger.debug(
        f"📊 API request for logs statistics (profile: '{profile}', time_range: '{time_range}', exclude: {exclude})"
    )
    stats = get_logs_stats(
        profile_filter=profile, time_range=time_range, exclude_domains=exclude
    )
    logger.info(f"📊 Returning stats: {stats}")
    return LogsStatsResponse(**stats)


@app.get("/logs", response_model=LogsResponse, tags=["Logs"])
async def get_dns_logs(  # pylint: disable=too-many-positional-arguments
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from results (supports wildcards: *.apple.com, tracking.*)",
    ),
    search: Optional[str] = Query(
        default="", description="Search query for domain names"
    ),
    status_filter: Optional[str] = Query(
        default="all", description="Filter by status: all, blocked, allowed"
    ),
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    devices: Optional[List[str]] = Query(
        default=None, description="Filter by specific device names"
    ),
    time_range: str = Query(
        default="all", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    limit: int = Query(
        default=100,
        ge=1,
        le=10000,
        description="Maximum number of records to return",
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    current_user: str = Depends(get_current_user),
):
    """
    Get DNS logs with optional filtering and pagination.

    - **exclude**: List of domains to exclude from results
    - **search**: Search query for domain names
    - **status**: Filter by status (all, blocked, allowed)
    - **profile**: Filter by specific profile ID
    - **devices**: Filter by specific device names
    - **time_range**: Time range filter (30m, 1h, 6h, 24h, 7d, 30d, 3m, all)
    - **limit**: Maximum number of records to return (1-10000)
    - **offset**: Number of records to skip for pagination
    """
    logger.debug(
        f"📊 API request: exclude={exclude}, search='{search}', "
        f"status={status_filter}, profile='{profile}', devices={devices}, "
        f"time_range='{time_range}', limit={limit}, offset={offset}"
    )

    logs, filtered_total_records = get_logs(
        exclude_domains=exclude,
        search_query=search,
        status_filter=status_filter,
        profile_filter=profile,
        device_filter=devices,
        time_range=time_range,
        limit=limit,
        offset=offset,
    )

    logger.info(
        f"📊 Returning {len(logs)} DNS logs from {filtered_total_records} filtered records"
    )

    return LogsResponse(
        data=logs,
        total_records=filtered_total_records,
        returned_records=len(logs),
        excluded_domains=exclude,
    )


@app.get("/profiles", response_model=ProfileListResponse, tags=["Profiles"])
async def list_available_profiles(current_user: str = Depends(get_current_user)):
    """Get list of available profiles with their record counts and last activity."""
    logger.debug("🧱 API request for available profiles")
    profiles = get_profiles_from_db()
    logger.info(f"🧱 Returning {len(profiles)} profiles")
    return ProfileListResponse(profiles=profiles, total_profiles=len(profiles))


@app.get("/profiles/info", response_model=ProfileInfoResponse, tags=["Profiles"])
async def get_profile_information(current_user: str = Depends(get_current_user)):
    """Get detailed information for all configured profiles from NextDNS API."""
    logger.debug("🧱 API request for profile information")

    configured_profiles = get_configured_profile_ids()
    if not configured_profiles:
        return ProfileInfoResponse(profiles={}, total_profiles=0)

    profile_info = get_multiple_profiles_info(configured_profiles)
    logger.info(f"🧱 Returning information for {len(profile_info)} profiles")

    return ProfileInfoResponse(profiles=profile_info, total_profiles=len(profile_info))


@app.get(
    "/profiles/{profile_id}/info",
    response_model=NextDNSProfileInfo,
    tags=["Profiles"],
)
async def get_single_profile_info(
    profile_id: str, current_user: str = Depends(get_current_user)
):
    """Get detailed information for a specific profile from NextDNS API."""
    logger.debug(f"🧱 API request for profile {profile_id} information")

    profile_info = get_profile_info(profile_id)
    if not profile_info:
        raise HTTPException(
            status_code=404,
            detail=f"Profile {profile_id} not found or could not be fetched",
        )

    logger.info(f"🧱 Returning information for profile {profile_id}")
    return NextDNSProfileInfo(**profile_info)


@app.get("/stats/overview", response_model=StatsOverviewResponse, tags=["Statistics"])
async def get_stats_overview(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from statistics (supports wildcards: *.apple.com, tracking.*)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get overview statistics for the dashboard."""
    logger.debug(
        f"📊 Stats overview request: profile={profile}, time_range={time_range}, exclude={exclude}"
    )

    # Get real data from database
    stats = get_db_stats_overview(
        profile_filter=profile, time_range=time_range, exclude_domains=exclude
    )
    return StatsOverviewResponse(**stats)


@app.get("/stats/timeseries", response_model=TimeSeriesResponse, tags=["Statistics"])
async def get_stats_timeseries(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    granularity: Optional[str] = Query(
        default=None,
        description="Data granularity: 5min, hour, day, week (auto if not specified)",
    ),
    group_by: str = Query(
        default="status",
        description="Group by: 'status' (blocked/allowed) or 'profile' (by profile_id)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get time series data for charts."""
    logger.debug(
        "📊 Time series request: profile=%s, time_range=%s, granularity=%s, group_by=%s",
        profile,
        time_range,
        granularity,
        group_by,
    )

    # Auto-determine granularity based on time range
    if not granularity:
        granularity_map = {
            "30m": "1min",
            "1h": "5min",
            "6h": "15min",
            "24h": "hour",
            "7d": "day",
            "30d": "day",
            "3m": "week",
            "all": "week",
        }
        granularity = granularity_map.get(time_range, "hour")

    # Get real time series data from database
    result = get_db_stats_timeseries(
        profile_filter=profile,
        time_range=time_range,
        granularity=granularity,
        group_by=group_by,
    )

    # Handle different return types based on group_by mode
    if group_by == "profile":
        # Result is a dict with data, granularity, total_points, available_profiles
        data_points = result.get("data", [])
        available_profiles = result.get("available_profiles", [])
        time_series_data = [TimeSeriesDataPoint(**point) for point in data_points]

        return TimeSeriesResponse(
            data=time_series_data,
            granularity=granularity,
            total_points=len(time_series_data),
            available_profiles=available_profiles,
        )

    # Legacy mode: result is a list of data points
    time_series_data = [TimeSeriesDataPoint(**point) for point in result]

    return TimeSeriesResponse(
        data=time_series_data,
        granularity=granularity,
        total_points=len(time_series_data),
    )


@app.get("/stats/domains", response_model=TopDomainsResponse, tags=["Statistics"])
async def get_top_domains(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    limit: int = Query(
        default=10, ge=5, le=50, description="Number of top domains to return"
    ),
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from results (supports wildcards: *.apple.com, tracking.*)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get top blocked and allowed domains."""
    logger.debug(
        f"📊 Top domains request: profile={profile}, time_range={time_range}, limit={limit}, exclude={exclude}"
    )

    # Get real domains data from database
    domains_data = get_db_top_domains(
        profile_filter=profile,
        time_range=time_range,
        limit=limit,
        exclude_domains=exclude,
    )

    # Convert to TopDomainsItem objects
    blocked_domains = [
        TopDomainsItem(**item) for item in domains_data["blocked_domains"]
    ]
    allowed_domains = [
        TopDomainsItem(**item) for item in domains_data["allowed_domains"]
    ]

    return TopDomainsResponse(
        blocked_domains=blocked_domains, allowed_domains=allowed_domains
    )


@app.get("/stats/tlds", response_model=TopTLDsResponse, tags=["Statistics"])
async def get_top_tlds(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    limit: int = Query(
        default=10, ge=5, le=50, description="Number of top TLDs to return"
    ),
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from results (supports wildcards: *.apple.com, tracking.*)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get top-level domain statistics (TLD aggregation).

    Groups all subdomains under their parent domains:
    - gateway.icloud.com → icloud.com
    - bag.itunes.apple.com → apple.com
    - www.google.com → google.com
    """
    logger.debug(
        f"📊 Top TLDs request: profile={profile}, time_range={time_range}, limit={limit}, exclude={exclude}"
    )

    # Get TLD aggregation data from database
    tlds_data = get_stats_tlds(
        profile_filter=profile,
        time_range=time_range,
        limit=limit,
        exclude_domains=exclude,
    )

    # Convert to TopDomainsItem objects (reusing same structure)
    blocked_tlds = [TopDomainsItem(**item) for item in tlds_data["blocked_tlds"]]
    allowed_tlds = [TopDomainsItem(**item) for item in tlds_data["allowed_tlds"]]

    return TopTLDsResponse(blocked_tlds=blocked_tlds, allowed_tlds=allowed_tlds)


@app.get("/devices", response_model=DeviceStatsResponse, tags=["Devices"])
async def get_devices(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    current_user: str = Depends(get_current_user),
):
    """Get available devices for device filtering.

    Returns device names and basic statistics for the specified profile and time range.
    This endpoint is optimized for populating device filter dropdowns.
    """
    logger.debug(f"📱 Devices request: profile={profile}, time_range={time_range}")

    # Get device statistics (reuse existing function but with higher limit)
    device_results = get_stats_devices(
        profile_filter=profile,
        time_range=time_range,
        limit=50,  # Get more devices for filtering
        exclude_devices=None,
    )

    # Convert to DeviceUsageItem objects
    devices = [DeviceUsageItem(**device) for device in device_results]

    return DeviceStatsResponse(devices=devices)


@app.get("/stats/devices", response_model=DeviceStatsResponse, tags=["Statistics"])
async def get_device_stats(
    profile: Optional[str] = Query(
        default=None, description="Filter by specific profile ID"
    ),
    time_range: str = Query(
        default="24h", description="Time range: 30m, 1h, 6h, 24h, 7d, 30d, 3m, all"
    ),
    limit: int = Query(
        default=10, ge=5, le=50, description="Number of top devices to return"
    ),
    exclude: Optional[List[str]] = Query(
        default=None,
        description="Device names to exclude from results (e.g. 'Unidentified Device')",
    ),
    exclude_domains: Optional[List[str]] = Query(
        default=None,
        description="Domains/patterns to exclude from results (supports wildcards: *.apple.com, tracking.*)",
    ),
    current_user: str = Depends(get_current_user),
):
    """Get device usage statistics showing DNS query activity by device.

    Shows which devices generate the most DNS traffic, with breakdown of blocked vs allowed queries.
    Useful for network monitoring, troubleshooting, and identifying device behavior patterns.
    """
    logger.debug(
        f"📱 Device stats request: profile={profile}, time_range={time_range}, "
        f"limit={limit}, exclude_devices={exclude}, exclude_domains={exclude_domains}"
    )

    # Get device statistics from database
    device_results = get_stats_devices(
        profile_filter=profile,
        time_range=time_range,
        limit=limit,
        exclude_devices=exclude,
        exclude_domains=exclude_domains,
    )

    # Convert to DeviceUsageItem objects
    devices = [DeviceUsageItem(**device) for device in device_results]

    return DeviceStatsResponse(devices=devices)


# ---------------------------------------------------------------------------
# Settings — NextDNS configuration (API key + profile management)
# ---------------------------------------------------------------------------


class ApiKeyResponse(BaseModel):
    """Masked API key response."""

    configured: bool
    masked_key: Optional[str] = None  # e.g. "••••••••ab12"


class ApiKeyUpdateRequest(BaseModel):
    """Request body for updating the NextDNS API key."""

    api_key: str


class SettingsProfileItem(BaseModel):
    """A single NextDNS profile entry from the settings table."""

    profile_id: str
    enabled: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class SettingsProfileListResponse(BaseModel):
    """List of configured NextDNS profiles from the settings table."""

    profiles: List[SettingsProfileItem]
    total: int


class AddProfileRequest(BaseModel):
    """Request body for adding a new profile."""

    profile_id: str


class UpdateProfileRequest(BaseModel):
    """Request body for enabling/disabling a profile."""

    enabled: bool


class DeleteProfileResponse(BaseModel):
    """Response after deleting a profile."""

    deleted: bool
    profile_id: str
    dns_logs_deleted: int
    fetch_status_deleted: int


def _mask_api_key(key: str) -> str:
    """Return a masked version of *key* showing only the last 4 characters."""
    if len(key) <= 4:
        return "••••"
    return "•" * (len(key) - 4) + key[-4:]


def _validate_nextdns_api_key(api_key: str) -> bool:
    """Check the key against the NextDNS API by listing profiles.

    Returns True if the key is accepted (HTTP 200), False otherwise.
    """
    try:
        response = __import__("requests").get(
            "https://api.nextdns.io/profiles",
            headers={"X-Api-Key": api_key},
            timeout=10,
        )
        return response.status_code == 200
    except Exception:  # pylint: disable=broad-exception-caught
        return False


@app.get(
    "/settings/nextdns/api-key",
    response_model=ApiKeyResponse,
    tags=["Settings"],
)
async def get_api_key_setting(
    current_user: str = Depends(get_current_user),
):
    """Return whether a NextDNS API key is configured and its masked value."""
    key = get_nextdns_api_key()
    if not key:
        return ApiKeyResponse(configured=False)
    return ApiKeyResponse(configured=True, masked_key=_mask_api_key(key))


@app.put(
    "/settings/nextdns/api-key",
    response_model=ApiKeyResponse,
    tags=["Settings"],
)
async def update_api_key_setting(
    body: ApiKeyUpdateRequest,
    current_user: str = Depends(get_current_user),
):
    """Validate the provided key against the NextDNS API and persist it."""
    api_key = body.api_key.strip()
    if not api_key:
        raise HTTPException(status_code=400, detail="api_key must not be empty")

    if not _validate_nextdns_api_key(api_key):
        raise HTTPException(
            status_code=422,
            detail="API key rejected by NextDNS — check that it is valid",
        )

    if not set_nextdns_api_key(api_key):
        raise HTTPException(status_code=500, detail="Failed to save API key")

    logger.info("🔑 NextDNS API key updated via settings endpoint")
    return ApiKeyResponse(configured=True, masked_key=_mask_api_key(api_key))


@app.get(
    "/settings/nextdns/profiles",
    response_model=SettingsProfileListResponse,
    tags=["Settings"],
)
async def list_settings_profiles(
    current_user: str = Depends(get_current_user),
):
    """Return all configured NextDNS profiles (enabled and disabled)."""
    rows = get_all_profiles()
    items = [
        SettingsProfileItem(
            profile_id=r.profile_id,
            enabled=r.enabled,
            created_at=r.created_at.isoformat() if r.created_at else None,
            updated_at=r.updated_at.isoformat() if r.updated_at else None,
        )
        for r in rows
    ]
    return SettingsProfileListResponse(profiles=items, total=len(items))


@app.post(
    "/settings/nextdns/profiles",
    response_model=SettingsProfileItem,
    status_code=status.HTTP_201_CREATED,
    tags=["Settings"],
)
async def add_settings_profile(
    body: AddProfileRequest,
    current_user: str = Depends(get_current_user),
):
    """Add a new NextDNS profile after validating it exists on NextDNS."""
    profile_id = body.profile_id.strip()
    if not profile_id:
        raise HTTPException(status_code=400, detail="profile_id must not be empty")

    # Verify the profile exists on NextDNS
    api_key = get_nextdns_api_key()
    if not api_key:
        raise HTTPException(
            status_code=422,
            detail="No NextDNS API key configured — set it via PUT /settings/nextdns/api-key first",
        )

    profile_info = get_profile_info(profile_id)
    if not profile_info or profile_info.get("error"):
        raise HTTPException(
            status_code=422,
            detail=f"Profile '{profile_id}' not found or not accessible with the current API key",
        )

    if not add_profile(profile_id):
        raise HTTPException(
            status_code=409,
            detail=f"Profile '{profile_id}' already exists",
        )

    row = get_profile(profile_id)
    return SettingsProfileItem(
        profile_id=row.profile_id,
        enabled=row.enabled,
        created_at=row.created_at.isoformat() if row.created_at else None,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@app.put(
    "/settings/nextdns/profiles/{profile_id}",
    response_model=SettingsProfileItem,
    tags=["Settings"],
)
async def update_settings_profile(
    profile_id: str,
    body: UpdateProfileRequest,
    current_user: str = Depends(get_current_user),
):
    """Enable or disable a NextDNS profile."""
    if not update_profile_enabled(profile_id, body.enabled):
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    row = get_profile(profile_id)
    return SettingsProfileItem(
        profile_id=row.profile_id,
        enabled=row.enabled,
        created_at=row.created_at.isoformat() if row.created_at else None,
        updated_at=row.updated_at.isoformat() if row.updated_at else None,
    )


@app.delete(
    "/settings/nextdns/profiles/{profile_id}",
    response_model=DeleteProfileResponse,
    tags=["Settings"],
)
async def delete_settings_profile(
    profile_id: str,
    purge_data: bool = Query(
        default=True,
        description="Also delete all DNS logs and fetch status for this profile",
    ),
    current_user: str = Depends(get_current_user),
):
    """Delete a profile and optionally purge all its DNS log data."""
    result = delete_profile(profile_id, delete_data=purge_data)
    if not result["deleted"]:
        raise HTTPException(
            status_code=404,
            detail=f"Profile '{profile_id}' not found",
        )
    return DeleteProfileResponse(
        deleted=True,
        profile_id=profile_id,
        dns_logs_deleted=result["dns_logs_deleted"],
        fetch_status_deleted=result["fetch_status_deleted"],
    )


# ---------------------------------------------------------------------------
# /settings/system — scheduler + application settings
# ---------------------------------------------------------------------------

VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


class SystemSettingsResponse(BaseModel):
    """Current scheduler and application settings."""

    fetch_interval: int
    fetch_limit: int
    log_level: str


class SystemSettingsUpdateRequest(BaseModel):
    """Partial update for scheduler / application settings."""

    fetch_interval: Optional[int] = None
    fetch_limit: Optional[int] = None
    log_level: Optional[str] = None


@app.get("/settings/system", response_model=SystemSettingsResponse, tags=["Settings"])
async def get_system_settings(
    current_user: str = Depends(get_current_user),
):
    """Return current scheduler and application settings."""
    return SystemSettingsResponse(
        fetch_interval=get_fetch_interval(),
        fetch_limit=get_fetch_limit(),
        log_level=get_log_level(),
    )


@app.put("/settings/system", response_model=SystemSettingsResponse, tags=["Settings"])
async def update_system_settings(
    body: SystemSettingsUpdateRequest,
    current_user: str = Depends(get_current_user),
):
    """Update scheduler and/or application settings. Changes take effect immediately."""
    if body.fetch_interval is not None:
        if not 1 <= body.fetch_interval <= 1440:
            raise HTTPException(
                status_code=422,
                detail="fetch_interval must be between 1 and 1440 minutes",
            )
        set_fetch_interval(body.fetch_interval)
        if apscheduler_instance is not None:
            try:
                apscheduler_instance.reschedule_job(
                    "fetch_logs",
                    trigger="interval",
                    minutes=body.fetch_interval,
                )
                logger.info(
                    f"⏰ Scheduler rescheduled to {body.fetch_interval} minutes"
                )
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.warning(f"⚠️  Could not reschedule job: {e}")

    if body.fetch_limit is not None:
        if not 10 <= body.fetch_limit <= 1000:
            raise HTTPException(
                status_code=422,
                detail="fetch_limit must be between 10 and 1000",
            )
        set_fetch_limit(body.fetch_limit)
        logger.info(f"📊 Fetch limit updated to {body.fetch_limit}")

    if body.log_level is not None:
        level = body.log_level.upper()
        if level not in VALID_LOG_LEVELS:
            raise HTTPException(
                status_code=422,
                detail=f"log_level must be one of: {', '.join(sorted(VALID_LOG_LEVELS))}",
            )
        set_log_level(level)
        apply_log_level(level)

    return SystemSettingsResponse(
        fetch_interval=get_fetch_interval(),
        fetch_limit=get_fetch_limit(),
        log_level=get_log_level(),
    )


if __name__ == "__main__":
    import uvicorn

    logger.info("🖥️  Starting FastAPI server with uvicorn on 0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
