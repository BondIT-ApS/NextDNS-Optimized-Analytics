# 05 - Configuration

## ⚙️ Environment Variables

Complete reference for configuring NextDNS Optimized Analytics.

## 🔐 NextDNS Configuration

### Required Settings
```env
# NextDNS API Integration
API_KEY=your_nextdns_api_key_here
PROFILE_IDS=profile1,profile2,profile3
```

### Getting Your API Key
1. Login to NextDNS dashboard
2. Navigate to Account → API
3. Generate new API key
4. Copy key to `API_KEY` environment variable

## 📊 Database Configuration

```env
# PostgreSQL Settings
POSTGRES_USER=nextdns_user
POSTGRES_PASSWORD=your_secure_password_here
POSTGRES_DB=nextdns
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

## 🔒 Security Configuration

```env
# Local API Authentication
LOCAL_API_KEY=your_secure_api_key_here

# Application Security
CORS_ORIGINS=http://localhost:5003,https://your-domain.com
```

## 📈 Performance Settings

```env
# Data Fetching
FETCH_INTERVAL=60       # Minutes between API calls
FETCH_LIMIT=1000        # Max records per fetch

# Logging
LOG_LEVEL=INFO          # DEBUG, INFO, WARNING, ERROR
```

---

**Next:** [Development Guide](./06-development.md)