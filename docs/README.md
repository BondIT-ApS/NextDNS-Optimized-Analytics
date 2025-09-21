# NextDNS Optimized Analytics Documentation

Welcome to the comprehensive documentation for NextDNS Optimized Analytics - a robust Docker-based solution that fetches, stores, and visualizes DNS logs from the NextDNS API with advanced filtering and analytics capabilities.

## 📚 Documentation Structure

| Document | Description |
|----------|-------------|
| [01 - Overview](./01-overview.md) | Solution overview, purpose, and key features |
| [02 - Architecture](./02-architecture.md) | System architecture, components, and data flow |
| [03 - API Reference](./03-api-reference.md) | Detailed API endpoints, authentication, and examples |
| [04 - Deployment](./04-deployment.md) | Deployment procedures and infrastructure options |
| [05 - Configuration](./05-configuration.md) | Environment variables, NextDNS setup, and security |
| [06 - Development](./06-development.md) | Local development setup, testing, and debugging |
| [07 - Troubleshooting](./07-troubleshooting.md) | Common issues, solutions, and diagnostic tools |
| [08 - Security](./08-security.md) | Security considerations and best practices |

## 🚀 Quick Start

1. **New to the solution?** → Start with [Overview](./01-overview.md)
2. **Ready to deploy?** → Follow [Deployment Guide](./04-deployment.md)
3. **Need to configure?** → Check [Configuration](./05-configuration.md)
4. **Development setup?** → Review [Development Guide](./06-development.md)
5. **API integration?** → Use [API Reference](./03-api-reference.md)

## 🔗 Key Resources

- **Docker Images**: 
  - [Backend](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-backend)
  - [Frontend](https://hub.docker.com/r/maboni82/nextdns-optimized-analytics-frontend)
- **GitHub Repository**: [NextDNS-Optimized-Analytics](https://github.com/BondIT-ApS/NextDNS-Optimized-Analytics)
- **NextDNS API**: [NextDNS Documentation](https://nextdns.io/api)

## 💡 Documentation Conventions

- **🔧** Configuration items and setup instructions
- **⚠️** Important warnings and gotchas
- **✅** Supported features and confirmed working setups
- **❌** Unsupported or deprecated features
- **📝** Code examples and configuration snippets
- **🐳** Docker-specific instructions
- **🔐** Security-related information
- **📊** Analytics and monitoring content

## 🎯 Key Features Covered

- **Real-time DNS Log Collection** from NextDNS API
- **Advanced Filtering** beyond standard NextDNS capabilities
- **Docker-based Deployment** with health monitoring
- **Interactive Web Dashboard** with real-time analytics
- **RESTful API** with FastAPI and automatic documentation
- **Multi-profile Support** for managing multiple NextDNS configurations
- **TLD Aggregation Analytics** - Group subdomains under parent domains
- **Device Usage Analytics** - Track DNS activity by device with exclusion support
- **Time Series Data** for charts and trend analysis
- **Comprehensive Logging** with configurable levels and monitoring

## 🤝 Contributing to Documentation

When updating documentation:
1. Follow the existing structure and numbering conventions
2. Update this index if adding new documents
3. Include practical examples and real-world scenarios
4. Test all code snippets and configurations
5. Use consistent emoji indicators for different content types
6. Keep security considerations prominent

## 🛠️ Quick Health Check

Before diving into documentation, verify your system is running:

```bash
# Check backend health
curl http://localhost:5001/health

# Check frontend accessibility  
curl http://localhost:5002

# View API documentation
open http://localhost:5001/docs
```

---
*Last updated: 2025-09-20*  
*Documentation version: v2.0*  
*Compatible with: NextDNS Analytics v2.0+*