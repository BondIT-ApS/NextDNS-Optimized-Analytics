# file: backend/main.py
import os
import platform
import secrets
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any

import psutil
from fastapi import FastAPI, Depends, HTTPException, Query, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Set up logging first
from logging_config import setup_logging, get_logger
from models import init_db, get_logs, get_total_record_count, get_logs_stats
from models import get_available_profiles as get_profiles_from_db
from models import (
    get_stats_overview as get_db_stats_overview,
    get_stats_timeseries as get_db_stats_timeseries,
    get_top_domains as get_db_top_domains,
    get_stats_tlds,
    get_stats_devices,
)
from profile_service import (
    get_profile_info,
    get_multiple_profiles_info,
    get_configured_profile_ids,
)

setup_logging()
logger = get_logger(__name__)

# Track application start time for accurate uptime
app_start_time = datetime.now(timezone.utc)

try:
    from scheduler import scheduler  # pylint: disable=unused-import,duplicate-code

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
    redoc_url="/redoc",
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
    blocked_queries: int
    allowed_queries: int


class TimeSeriesResponse(BaseModel):
    """Response model for time series data."""

    data: List[TimeSeriesDataPoint]
    granularity: str
    total_points: int


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
        "total_dns_records": total_records,
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Simple health check endpoint."""
    try:
        # Quick database check
        total_records = get_total_record_count()
        db_healthy = total_records >= 0

        return HealthResponse(
            status="healthy" if db_healthy else "unhealthy", healthy=db_healthy
        )
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(f"❌ Health check failed: {e}")
        return HealthResponse(status="unhealthy", healthy=False)


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
        disk = psutil.disk_usage("/")
        current_time = datetime.now(timezone.utc)
        uptime_seconds = (current_time - app_start_time).total_seconds()

        # Get environment variables
        fetch_interval = int(os.getenv("FETCH_INTERVAL", "60"))
        log_level = os.getenv("LOG_LEVEL", "INFO")

        system_resources = SystemResources(
            cpu_percent=cpu_percent,
            memory_total=memory.total,
            memory_available=memory.available,
            memory_percent=memory.percent,
            disk_total=disk.total,
            disk_used=disk.used,
            disk_percent=(disk.used / disk.total) * 100,
            uptime_seconds=uptime_seconds,
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
                "state_management": "TanStack Query 5.56.2",
            },
        }

        api_healthy = True  # API is responding if we get here
        overall_healthy = db_healthy and api_healthy

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
            system_resources=system_resources,
            server_info=server_info,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

    except Exception as e:  # pylint: disable=broad-exception-caught
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
                uptime_seconds=0.0,
            ),
            server_info={"error": str(e)},
            timestamp=datetime.now(timezone.utc).isoformat(),
        )


@app.get("/stats", response_model=StatsResponse, tags=["Statistics"])
async def get_stats():
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
):
    """Get statistics for DNS logs in the database, optionally filtered by profile and time range."""
    logger.debug(
        f"📊 API request for logs statistics (profile: '{profile}', time_range: '{time_range}')"
    )
    stats = get_logs_stats(profile_filter=profile, time_range=time_range)
    logger.info(f"📊 Returning stats: {stats}")
    return LogsStatsResponse(**stats)


@app.get("/logs", response_model=LogsResponse, tags=["Logs"])
async def get_dns_logs(  # pylint: disable=too-many-positional-arguments
    exclude: Optional[List[str]] = Query(
        default=None, description="Domains to exclude from results"
    ),
    search: Optional[str] = Query(
        default="", description="Search query for domain names"
    ),
    status: Optional[str] = Query(
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
        default=100, ge=1, le=10000, description="Maximum number of records to return"
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
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
        f"status={status}, profile='{profile}', devices={devices}, time_range='{time_range}', limit={limit}, offset={offset}"
    )

    logs = get_logs(
        exclude_domains=exclude,
        search_query=search,
        status_filter=status,
        profile_filter=profile,
        device_filter=devices,
        time_range=time_range,
        limit=limit,
        offset=offset,
    )
    total_records = get_total_record_count()

    logger.info(f"📊 Returning {len(logs)} DNS logs")

    return LogsResponse(
        data=logs,
        total_records=total_records,
        returned_records=len(logs),
        excluded_domains=exclude,
    )


@app.get("/profiles", response_model=ProfileListResponse, tags=["Profiles"])
async def list_available_profiles():
    """Get list of available profiles with their record counts and last activity."""
    logger.debug("🧱 API request for available profiles")
    profiles = get_profiles_from_db()
    logger.info(f"🧱 Returning {len(profiles)} profiles")
    return ProfileListResponse(profiles=profiles, total_profiles=len(profiles))


@app.get("/profiles/info", response_model=ProfileInfoResponse, tags=["Profiles"])
async def get_profile_information():
    """Get detailed information for all configured profiles from NextDNS API."""
    logger.debug("🧱 API request for profile information")

    configured_profiles = get_configured_profile_ids()
    if not configured_profiles:
        return ProfileInfoResponse(profiles={}, total_profiles=0)

    profile_info = get_multiple_profiles_info(configured_profiles)
    logger.info(f"🧱 Returning information for {len(profile_info)} profiles")

    return ProfileInfoResponse(profiles=profile_info, total_profiles=len(profile_info))


@app.get(
    "/profiles/{profile_id}/info", response_model=NextDNSProfileInfo, tags=["Profiles"]
)
async def get_single_profile_info(profile_id: str):
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
):
    """Get overview statistics for the dashboard."""
    logger.debug(
        f"📊 Stats overview request: profile={profile}, time_range={time_range}"
    )

    # Get real data from database
    stats = get_db_stats_overview(profile_filter=profile, time_range=time_range)
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
):
    """Get time series data for charts."""
    logger.debug(
        f"📊 Time series request: profile={profile}, time_range={time_range}, granularity={granularity}"
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
    data_points = get_db_stats_timeseries(
        profile_filter=profile, time_range=time_range, granularity=granularity
    )

    # Convert to TimeSeriesDataPoint objects
    time_series_data = [TimeSeriesDataPoint(**point) for point in data_points]

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
):
    """Get top blocked and allowed domains."""
    logger.debug(
        f"📊 Top domains request: profile={profile}, time_range={time_range}, limit={limit}"
    )

    # Get real domains data from database
    domains_data = get_db_top_domains(
        profile_filter=profile, time_range=time_range, limit=limit
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
):
    """Get top-level domain statistics (TLD aggregation).

    Groups all subdomains under their parent domains:
    - gateway.icloud.com → icloud.com
    - bag.itunes.apple.com → apple.com
    - www.google.com → google.com
    """
    logger.debug(
        f"📊 Top TLDs request: profile={profile}, time_range={time_range}, limit={limit}"
    )

    # Get TLD aggregation data from database
    tlds_data = get_stats_tlds(
        profile_filter=profile, time_range=time_range, limit=limit
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
):
    """Get device usage statistics showing DNS query activity by device.

    Shows which devices generate the most DNS traffic, with breakdown of blocked vs allowed queries.
    Useful for network monitoring, troubleshooting, and identifying device behavior patterns.
    """
    logger.debug(
        f"📱 Device stats request: profile={profile}, time_range={time_range}, limit={limit}, exclude={exclude}"
    )

    # Get device statistics from database
    device_results = get_stats_devices(
        profile_filter=profile,
        time_range=time_range,
        limit=limit,
        exclude_devices=exclude,
    )

    # Convert to DeviceUsageItem objects
    devices = [DeviceUsageItem(**device) for device in device_results]

    return DeviceStatsResponse(devices=devices)


if __name__ == "__main__":
    import uvicorn

    logger.info("🖥️  Starting FastAPI server with uvicorn on 0.0.0.0:5000")
    uvicorn.run(app, host="0.0.0.0", port=5000, log_level="info")
