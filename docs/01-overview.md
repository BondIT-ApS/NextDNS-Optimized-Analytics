# 01 - Overview

## 🧱 NextDNS Optimized Analytics

NextDNS Optimized Analytics is a comprehensive Docker-based solution that transforms how you interact with NextDNS logs. Like building a sophisticated LEGO masterpiece, this system assembles NextDNS data into something greater than the sum of its parts.

## 🎯 Purpose

The NextDNS web dashboard provides basic analytics, but lacks advanced filtering and long-term data retention capabilities. This solution bridges that gap by:

- **Fetching** DNS logs from NextDNS API automatically
- **Storing** them locally in PostgreSQL for persistence  
- **Providing** advanced filtering beyond NextDNS standard capabilities
- **Visualizing** data through a modern React-based dashboard
- **Exposing** comprehensive REST API for custom integrations

## 🚀 Key Features

### **🔄 Automated Data Collection**
- **Real-time sync** with NextDNS API
- **Configurable intervals** (1-60 minutes)
- **Multi-profile support** for complex setups
- **Smart deduplication** prevents duplicate records
- **Error recovery** with automatic retry logic

### **📊 Advanced Analytics**
- **Domain exclusion filtering** (filter out noise like CDNs)
- **Time-range queries** with flexible date filtering
- **Query type analysis** (A, AAAA, CNAME, MX, etc.)
- **Block/Allow ratios** and trending analysis
- **Device-specific insights** when available
- **Geolocation data** for query sources

### **🐳 Modern Infrastructure**
- **Docker-based deployment** with health monitoring
- **FastAPI backend** with automatic OpenAPI documentation
- **React frontend** with TypeScript and modern tooling
- **PostgreSQL database** for reliable data storage
- **Nginx reverse proxy** with optimized caching
- **Comprehensive logging** with configurable levels

### **🔐 Security & Privacy**
- **Local data storage** - your DNS logs never leave your infrastructure
- **API key authentication** for all endpoints
- **Environment-based configuration** with secure defaults
- **CORS protection** and security headers
- **Health monitoring** for all components

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   NextDNS API   │───▶│  Backend API    │───▶│   PostgreSQL    │
│                 │    │   (FastAPI)     │    │   Database      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐
│  Web Dashboard  │◀───│  Nginx Proxy    │
│   (React/TS)    │    │                 │
└─────────────────┘    └─────────────────┘
```

## 🎪 What Makes This Special?

### **Beyond Standard NextDNS Capabilities**
- **Long-term storage**: Keep logs as long as you want
- **Advanced filtering**: Exclude domains, filter by device, time ranges
- **Custom queries**: Build complex analytics queries
- **Data export**: Get your data in JSON, CSV, or via API
- **Real-time monitoring**: Health checks and system metrics

### **Developer-Friendly**
- **Interactive API docs** at `/docs` endpoint
- **Type-safe TypeScript** frontend with modern React
- **Comprehensive logging** with debug modes
- **Docker health checks** for monitoring integration
- **Environment-based config** for different deployments

### **Production Ready**
- **ASGI server** (uvicorn) for high performance
- **Database migrations** handled automatically
- **Graceful error handling** with proper HTTP status codes
- **Resource monitoring** with system metrics
- **Multi-environment support** (development, staging, production)

## 🎯 Use Cases

### **Home Network Monitoring**
- Track which devices are generating most DNS queries
- Identify potentially malicious domains before they're blocked
- Monitor DNS-over-HTTPS vs standard DNS usage
- Analyze peak usage times and patterns

### **Small Business Analytics**
- Compliance reporting for DNS usage
- Employee device monitoring and policy enforcement
- Bandwidth optimization through DNS pattern analysis
- Security incident investigation and forensics

### **Developer Integration**
- Build custom dashboards and reporting tools
- Integrate DNS analytics into existing monitoring systems
- Create automated alerting based on DNS patterns
- Develop custom filtering and analysis algorithms

## 📊 Sample Analytics Insights

The system provides rich analytics capabilities:

```json
{
  "total_queries": 25847,
  "blocked_queries": 3241,
  "blocked_percentage": 12.5,
  "top_domains": ["google.com", "apple.com", "microsoft.com"],
  "top_blocked": ["ads.example.com", "tracker.com"],
  "query_types": {"A": 18456, "AAAA": 6234, "CNAME": 987},
  "hourly_patterns": "Peak usage 9AM-5PM weekdays"
}
```

## 🔍 Coming from NextDNS Dashboard?

If you're used to the NextDNS web interface, here's what's different:

| NextDNS Dashboard | NextDNS Optimized Analytics |
|-------------------|------------------------------|
| ✅ Basic query logs | ✅ **Enhanced query logs with filtering** |
| ✅ Simple blocking stats | ✅ **Detailed analytics and trends** |
| ❌ Limited data retention | ✅ **Unlimited local storage** |
| ❌ No domain exclusion | ✅ **Advanced domain filtering** |
| ❌ No API access | ✅ **Full REST API with docs** |
| ❌ Basic export | ✅ **Flexible data export options** |

## 🚦 Getting Started

Ready to build your NextDNS analytics foundation? Here's your roadmap:

1. **📖 Understand the system** → Continue reading [Architecture](./02-architecture.md)
2. **🚀 Deploy the solution** → Jump to [Deployment](./04-deployment.md)  
3. **⚙️ Configure your setup** → Review [Configuration](./05-configuration.md)
4. **🔌 Use the API** → Explore [API Reference](./03-api-reference.md)

## 💡 Philosophy

Just like LEGO bricks, this solution is built on the principle that simple, well-designed components can be combined to create something powerful and flexible. Each service (backend, frontend, database) is a discrete "brick" that connects perfectly with others while maintaining its own clear responsibility.

The result? A system that's easy to understand, modify, and extend - whether you're a home user wanting better DNS visibility or a developer building custom analytics solutions.

---

**Next:** [System Architecture](./02-architecture.md) → Understanding how the pieces fit together