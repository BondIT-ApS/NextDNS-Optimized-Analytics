# 07 - Troubleshooting

## 🔍 Common Issues and Solutions

Comprehensive troubleshooting guide for NextDNS Optimized Analytics.

## 🏥 Health Check Issues

### Container Shows "Unhealthy"

**Problem:** Portainer or Docker shows container as unhealthy.

**Solution:**
1. Check health endpoint manually:
```bash
curl http://localhost:5002/health
curl http://localhost:5003
```

2. Verify healthcheck configuration in container:
```bash
docker inspect container_name --format='{{json .Config.Healthcheck}}'
```

3. Check container logs:
```bash
docker logs container_name
```

## 🔌 API Connection Issues

### 401 Unauthorized Errors

**Problem:** API returns 401 when accessing protected endpoints.

**Cause:** Authentication is enabled but no valid JWT token provided.

**Solutions:**
```bash
# 1. Check if authentication is enabled
curl http://localhost:5002/auth/config

# 2. If enabled, login to get token
curl -X POST http://localhost:5002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'

# 3. Use token in requests
curl -H "Authorization: Bearer your_jwt_token" http://localhost:5002/stats

# 4. Verify authentication environment variables
docker exec backend-container env | grep AUTH_
```

### Login Failed / Invalid Credentials

**Problem:** Cannot login with username and password.

**Solutions:**
```bash
# Check authentication configuration
docker exec backend-container env | grep AUTH_

# Verify AUTH_PASSWORD is set
docker logs backend-container | grep "AUTH_PASSWORD"

# Check backend logs for authentication errors
docker logs backend-container | grep "Authentication failed"
```

### JWT Token Expired

**Problem:** Token works initially but then returns 401 errors.

**Cause:** JWT tokens expire after the configured session timeout.

**Solutions:**
```bash
# Check session timeout configuration
curl http://localhost:5002/auth/config

# Login again to get new token
curl -X POST http://localhost:5002/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your_password"}'
```

### Database Connection Failed

**Problem:** Backend cannot connect to database.

**Diagnostic Steps:**
```bash
# Check database container status
docker ps | grep postgres

# Test database connection
docker exec db-container pg_isready -U nextdns_user -d nextdns

# Check network connectivity
docker exec backend-container ping db-container
```

## 🌐 Frontend Issues

### Frontend Not Loading

**Problem:** Web interface returns 404 or connection refused.

**Solutions:**
1. Verify nginx configuration:
```bash
docker exec frontend-container nginx -t
```

2. Check port mapping:
```bash
docker ps | grep frontend
```

3. Test direct nginx access:
```bash
curl -I http://localhost:5003
```

## 📊 Data Issues

### No DNS Logs Appearing

**Problem:** Database remains empty despite running system.

**Diagnostic Steps:**
```bash
# Check NextDNS API connectivity
curl -H "X-API-Key: your_api_key" https://api.nextdns.io/profiles

# Verify fetch interval settings
curl http://localhost:5002/health/detailed | jq .fetch_interval_minutes

# Check backend logs for errors
docker logs backend-container | grep -i error
```

### High Resource Usage

**Problem:** System consuming excessive CPU/memory.

**Solutions:**
1. Adjust fetch interval:
```env
FETCH_INTERVAL=60  # Increase interval
```

2. Limit fetch size:
```env
FETCH_LIMIT=500   # Reduce batch size
```

3. Monitor resource usage:
```bash
curl http://localhost:5002/health/detailed | jq .system_resources
```

## 🐳 Docker Issues

### Port Conflicts

**Problem:** Ports already in use.

**Solutions:**
```bash
# Check port usage
lsof -i :3000
lsof -i :5001

# Change ports in docker-compose.yml
ports:
  - "8080:80"    # Frontend
  - "8081:5000"  # Backend
```

### Volume Permission Issues

**Problem:** Database volume permission errors.

**Solutions:**
```bash
# Fix volume permissions
docker-compose down
docker volume rm nextdns_db_data
docker-compose up -d
```

## 📝 Logging and Debugging

### Enable Debug Logging

```env
LOG_LEVEL=DEBUG
```

### View Comprehensive Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# With timestamps
docker-compose logs -f -t
```

### Health Check Script

```bash
#!/bin/bash
# comprehensive-health-check.sh

echo "🔍 Comprehensive Health Check"

# Backend API
echo "Testing Backend API..."
curl -f http://localhost:5002/health || echo "❌ Backend unhealthy"

# Frontend
echo "Testing Frontend..."
curl -f http://localhost:5003 || echo "❌ Frontend unavailable"

# Database
echo "Testing Database..."
docker exec db-container pg_isready -U nextdns_user -d nextdns || echo "❌ Database unavailable"

# API Authentication
echo "Testing API Authentication..."
curl http://localhost:5002/auth/config || echo "❌ Auth config unavailable"

# If auth is enabled, test login
AUTH_ENABLED=$(curl -s http://localhost:5002/auth/config | jq -r '.enabled')
if [ "$AUTH_ENABLED" = "true" ]; then
    echo "Authentication is enabled, testing login..."
    curl -X POST http://localhost:5002/auth/login \
      -H "Content-Type: application/json" \
      -d '{"username": "admin", "password": "'$AUTH_PASSWORD'"}' || echo "❌ Login failed"
else
    echo "✅ Authentication is disabled"
fi

echo "✅ Health check completed"
```

---

**Next:** [Security](./08-security.md)