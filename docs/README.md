# NextDNS Optimized Analytics Documentation

Welcome to the NextDNS Optimized Analytics documentation! This directory contains all documentation related to the project.

## 📚 **Documentation Index**

### **API Documentation**
- [**API Migration Guide**](API_MIGRATION.md) - Complete migration from Flask to FastAPI v2.0
- [**Health Endpoints**](health-endpoints.md) - Health check endpoints documentation

### **Configuration**
- [**Environment Variables**](environment-variables.md) - All configurable environment variables
- [**Docker Setup**](docker-setup.md) - Docker configuration and deployment

### **Development**
- [**Development Guide**](development-guide.md) - Setting up development environment
- [**Logging**](logging.md) - Logging configuration and best practices

## 🚀 **Quick Start**

1. **Check System Health**
   ```bash
   # Simple health check
   curl http://localhost:5001/health
   
   # Detailed system information  
   curl http://localhost:5001/health/detailed
   ```

2. **View Interactive API Docs**
   - Swagger UI: http://localhost:5001/docs
   - ReDoc: http://localhost:5001/redoc

3. **Monitor Database**
   ```bash
   # Get database statistics (requires auth)
   curl -u admin:your_api_key http://localhost:5001/stats
   ```

## 🎯 **Key Features**

- **FastAPI v2.0** with automatic OpenAPI documentation
- **Enhanced logging** with configurable levels and database statistics
- **Configurable data fetching** intervals
- **Comprehensive health monitoring** with system resource tracking
- **Real-time DNS log analytics** from NextDNS

## 🔧 **Configuration Overview**

```env
# Core Configuration
LOG_LEVEL=DEBUG              # Logging level
FETCH_INTERVAL=60           # Data fetch interval (minutes)
LOCAL_API_KEY=your_key      # API authentication

# NextDNS Integration
API_KEY=nextdns_api_key
PROFILE_ID=nextdns_profile

# Database
POSTGRES_USER=nextdns_user
POSTGRES_PASSWORD=password
POSTGRES_DB=nextdns
POSTGRES_HOST=db
```

## 📊 **Health Monitoring**

The system provides comprehensive health monitoring:

### **Simple Health Check** (`/health`)
- Quick database connectivity check
- Boolean healthy status
- Minimal response for monitoring systems

### **Detailed Health Check** (`/health/detailed`)
- API status (`status_api`)
- Database status (`status_db`) 
- Total DNS records count
- System resource utilization (CPU, memory, disk)
- Server information (platform, architecture, uptime)
- Configuration details (fetch interval, log level)
- Timestamp for monitoring

## 🐳 **Docker Deployment**

The application runs on modern ASGI server (uvicorn) for optimal performance:

```dockerfile
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000", "--log-level", "info"]
```

## 🔍 **Monitoring & Observability**

- **Enhanced logging** with emoji indicators for quick visual scanning
- **Database record tracking** with before/after statistics
- **System resource monitoring** via psutil integration
- **Real-time health checks** with comprehensive system information
- **Structured logging** for easy parsing and analysis

---

For detailed information about each topic, see the individual documentation files in this directory.