# 06 - Development

## 🛠️ Local Development Setup

Setting up NextDNS Optimized Analytics for local development and testing.

## 📋 Prerequisites

- Docker & Docker Compose
- Node.js 18+ (for frontend development)
- Python 3.13+ (for backend development)
- PostgreSQL 15+ (for database development)

## 🚀 Quick Development Setup

```bash
# Clone repository
git clone https://github.com/BondIT-ApS/NextDNS-Optimized-Analytics.git
cd NextDNS-Optimized-Analytics

# Setup environment
cp config/.env.template config/.env
# Edit config/.env with your development settings

# Start development stack
docker-compose up -d

# View logs
docker-compose logs -f
```

## 🔧 Development Workflow

1. **Backend Development**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

2. **Frontend Development**
```bash
cd frontend
npm install
npm run dev
```

3. **Database Development**
```bash
# Connect to development database
docker exec -it nextdns-db psql -U nextdns_user -d nextdns
```

## 🧪 Testing

```bash
# Run backend tests
python -m pytest backend/tests/

# Run frontend tests
cd frontend && npm test

# Integration tests
./scripts/test_1000_dns_queries.sh
```

---

**Next:** [Troubleshooting](./07-troubleshooting.md)