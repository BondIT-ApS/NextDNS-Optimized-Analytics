# Health Endpoints Documentation

This document describes the health monitoring endpoints available in the NextDNS Optimized Analytics API.

## 🏥 **Health Check Endpoints**

### **Simple Health Check**
`GET /health`

**Description:** Basic health check endpoint for monitoring systems and load balancers.

**Authentication:** None required

**Response Model:**
```json
{
  "status": "healthy|unhealthy",
  "healthy": boolean
}
```

**Example Response:**
```json
{
  "status": "healthy",
  "healthy": true
}
```

**Use Cases:**
- Load balancer health checks
- Basic monitoring systems
- Quick status verification
- Container orchestration health probes

---

### **Detailed Health Check**
`GET /health/detailed`

**Description:** Comprehensive health check with detailed system information and resource monitoring.

**Authentication:** None required

**Response Model:**
```json
{
  "status_api": "healthy|unhealthy",
  "status_db": "healthy|unhealthy", 
  "healthy": boolean,
  "total_dns_records": integer,
  "fetch_interval_minutes": integer,
  "log_level": "DEBUG|INFO|WARNING|ERROR|CRITICAL",
  "system_resources": {
    "cpu_percent": float,
    "memory_total": integer,
    "memory_available": integer,
    "memory_percent": float,
    "disk_total": integer,
    "disk_used": integer,
    "disk_percent": float,
    "uptime_seconds": float
  },
  "server_info": {
    "platform": "Linux|Darwin|Windows",
    "platform_release": string,
    "architecture": string,
    "hostname": string,
    "python_version": string,
    "cpu_count": integer,
    "cpu_count_logical": integer
  },
  "timestamp": "ISO 8601 timestamp"
}
```

**Example Response:**
```json
{
  "status_api": "healthy",
  "status_db": "healthy",
  "healthy": true,
  "total_dns_records": 515,
  "fetch_interval_minutes": 60,
  "log_level": "DEBUG",
  "system_resources": {
    "cpu_percent": 0.1,
    "memory_total": 8218316800,
    "memory_available": 6324994048,
    "memory_percent": 23.0,
    "disk_total": 62671097856,
    "disk_used": 26991333376,
    "disk_percent": 43.07,
    "uptime_seconds": 188855.04
  },
  "server_info": {
    "platform": "Linux",
    "platform_release": "6.10.14-linuxkit",
    "architecture": "aarch64",
    "hostname": "ecbfbba699e7",
    "python_version": "3.11.13",
    "cpu_count": 8,
    "cpu_count_logical": 8
  },
  "timestamp": "2025-09-18T08:06:55.037854+00:00"
}
```

---

## 📊 **Response Fields Explained**

### **Status Fields**
- **`status_api`**: API server health status
  - `"healthy"` - API is responding normally
  - `"unhealthy"` - API has issues or errors

- **`status_db`**: Database connection health
  - `"healthy"` - Database is accessible and responding
  - `"unhealthy"` - Database connection issues
  - `"unknown"` - Unable to determine database status

- **`healthy`**: Overall system health
  - `true` - Both API and database are healthy
  - `false` - One or more components are unhealthy

### **Application Metrics**
- **`total_dns_records`**: Total number of DNS log records in database
- **`fetch_interval_minutes`**: Configured interval for fetching new DNS logs from NextDNS
- **`log_level`**: Current logging level configuration

### **System Resources**
- **`cpu_percent`**: Current CPU utilization percentage
- **`memory_total`**: Total system memory in bytes
- **`memory_available`**: Available system memory in bytes  
- **`memory_percent`**: Memory utilization percentage
- **`disk_total`**: Total disk space in bytes
- **`disk_used`**: Used disk space in bytes
- **`disk_percent`**: Disk utilization percentage
- **`uptime_seconds`**: System uptime in seconds

### **Server Information**
- **`platform`**: Operating system (Linux, Darwin, Windows)
- **`platform_release`**: OS version/release
- **`architecture`**: CPU architecture (x86_64, aarch64, etc.)
- **`hostname`**: Server hostname
- **`python_version`**: Python runtime version
- **`cpu_count`**: Physical CPU cores
- **`cpu_count_logical`**: Logical CPU cores (including hyperthreading)

---

## 🔧 **Usage Examples**

### **Basic Health Check**
```bash
# Simple curl request
curl http://localhost:5001/health

# With jq for formatted output
curl -s http://localhost:5001/health | jq

# Check exit code for monitoring
curl -f http://localhost:5001/health && echo "Healthy" || echo "Unhealthy"
```

### **Detailed Health Check**
```bash
# Get comprehensive system information
curl http://localhost:5001/health/detailed

# Extract specific metrics
curl -s http://localhost:5001/health/detailed | jq '.total_dns_records'
curl -s http://localhost:5001/health/detailed | jq '.system_resources.cpu_percent'
curl -s http://localhost:5001/health/detailed | jq '.server_info.platform'

# Check database status specifically
curl -s http://localhost:5001/health/detailed | jq -r '.status_db'
```

### **Monitoring Scripts**
```bash
#!/bin/bash
# Simple monitoring script

HEALTH=$(curl -s http://localhost:5001/health)
STATUS=$(echo $HEALTH | jq -r '.status')

if [ "$STATUS" = "healthy" ]; then
    echo "✅ System is healthy"
    exit 0
else
    echo "❌ System is unhealthy"
    exit 1
fi
```

---

## 🚨 **Error Handling**

### **Database Connection Issues**
If the database is unreachable, the endpoints will return:

**Simple Health:**
```json
{
  "status": "unhealthy",
  "healthy": false
}
```

**Detailed Health:**
```json
{
  "status_api": "healthy",
  "status_db": "unhealthy",
  "healthy": false,
  "total_dns_records": 0,
  ...
}
```

### **System Resource Monitoring Errors**
If system resource monitoring fails, the detailed endpoint will return minimal error information:

```json
{
  "status_api": "unhealthy",
  "status_db": "unknown",
  "healthy": false,
  "system_resources": {
    "cpu_percent": 0.0,
    "memory_total": 0,
    ...
  },
  "server_info": {
    "error": "Error message"
  },
  ...
}
```

---

## 📈 **Monitoring Integration**

### **Prometheus Metrics**
The health endpoints provide data that can be easily converted to Prometheus metrics:

```bash
# CPU utilization
cpu_usage_percent{instance="nextdns-analytics"}

# Memory utilization  
memory_usage_percent{instance="nextdns-analytics"}

# Database records
dns_records_total{instance="nextdns-analytics"}

# Health status
service_health{service="api",instance="nextdns-analytics"}
service_health{service="database",instance="nextdns-analytics"}
```

### **Load Balancer Configuration**
```nginx
# Nginx upstream health check
upstream nextdns_backend {
    server backend:5000;
    # Health check configuration
    location /health {
        access_log off;
        return 200;
    }
}
```

### **Docker Health Check**
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:5000/health || exit 1
```

---

## 🎯 **Best Practices**

1. **Use Simple Health Check** for:
   - Load balancer health probes
   - Container orchestration (Kubernetes, Docker Swarm)
   - Basic monitoring systems

2. **Use Detailed Health Check** for:
   - Operational dashboards
   - Detailed system monitoring
   - Troubleshooting and debugging
   - Resource planning and capacity management

3. **Monitoring Frequency**:
   - Simple health checks: Every 10-30 seconds
   - Detailed health checks: Every 1-5 minutes

4. **Alerting Thresholds**:
   - CPU usage > 80%
   - Memory usage > 85%
   - Disk usage > 90%
   - Database connectivity issues