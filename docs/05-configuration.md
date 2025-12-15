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

## 🔒 Authentication Configuration

### JWT-Based Authentication (Optional)

Authentication is **disabled by default** for ease of local development. Enable it for production deployments.

```env
# Enable/Disable Authentication
AUTH_ENABLED=false              # Set to 'true' to enable authentication

# Authentication Credentials
AUTH_USERNAME=admin             # Username for login (default: admin)
AUTH_PASSWORD=your_password     # Password (plain text or bcrypt hash)

# JWT Token Configuration
AUTH_SECRET_KEY=your_secret_key_minimum_32_chars  # Secret key for JWT signing
AUTH_SESSION_TIMEOUT=60         # Session timeout in minutes (default: 60)
```

### Authentication Setup Guide

**1. Generate a Secure Secret Key:**
```bash
# Generate random 64-character hex string
openssl rand -hex 32

# Or use Python
python3 -c "import secrets; print(secrets.token_hex(32))"
```

**2. Set Password:**
- Use plain text password (will be compared directly)
- Or use bcrypt hash for enhanced security:
```bash
# Generate bcrypt hash
python3 -c "from passlib.hash import bcrypt; print(bcrypt.hash('your_password'))"
```

**3. Enable Authentication:**
```env
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD=your_secure_password_or_bcrypt_hash
AUTH_SECRET_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6
AUTH_SESSION_TIMEOUT=60
```

### Security Recommendations

- ⚠️ **Never use default values in production**
- 🔑 Generate unique `AUTH_SECRET_KEY` (minimum 32 characters)
- 🔐 Use strong passwords (12+ characters, mixed case, numbers, symbols)
- ⏱️ Adjust session timeout based on your security requirements
- 📦 For production, consider using bcrypt password hashes

## 🛡️ Application Security

```env
# CORS Configuration
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