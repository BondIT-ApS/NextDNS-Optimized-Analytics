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

## 🧪 Testing Infrastructure

Comprehensive testing setup with unit tests, integration tests, and code coverage reporting.

### Backend Testing (Python + pytest)

**Test Structure:**
```
backend/
├── tests/
│   ├── conftest.py              # Shared fixtures
│   ├── unit/                    # Unit tests
│   │   └── test_models.py       # Database models
│   ├── integration/             # Integration tests
│   │   └── test_api_health.py   # API endpoints
│   └── fixtures/                # Test data
└── pytest.ini                   # Pytest configuration
```

**Running Backend Tests:**
```bash
# Install dev dependencies
cd backend
pip install -r requirements-dev.txt

# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=. --cov-report=html --cov-report=term

# Run specific test types
pytest tests/unit/ -v
pytest tests/integration/ -v

# View coverage report
open htmlcov/index.html
```

**Backend Coverage Target:** ≥70%

### Frontend Testing (TypeScript + Vitest)

**Test Structure:**
```
frontend/src/
├── __tests__/
│   ├── components/              # Component tests
│   ├── hooks/                   # Hook tests
│   └── utils/                   # Utility tests
│       └── utils.test.ts
└── test/
    └── setup.ts                 # Test setup
```

**Running Frontend Tests:**
```bash
# Navigate to frontend
cd frontend

# Run tests in watch mode
npm test

# Run tests once
npm run test -- --run

# Run with coverage
npm run test:coverage

# Run with UI
npm run test:ui
```

**Frontend Coverage Target:** ≥75%

### Integration Tests

```bash
# Run DNS query integration test
./scripts/test_1000_dns_queries.sh

# Test with Docker
docker-compose up -d
# Wait for services to be healthy
curl http://localhost:5001/health
curl http://localhost:5002/
```

### CI/CD Testing

All tests run automatically in GitHub Actions on PR creation:
- ✅ Backend unit & integration tests
- ✅ Frontend unit & component tests
- 📊 Codecov coverage upload
- 🛡️ Security scanning (Safety, Bandit)
- 🎨 Code quality checks (linting, formatting)

### Writing Tests

**Backend Test Example:**
```python
# tests/unit/test_models.py
import pytest
from models import extract_tld

def test_extract_tld():
    assert extract_tld("www.google.com") == "google.com"
    assert extract_tld("api.github.com") == "github.com"
```

**Frontend Test Example:**
```typescript
// __tests__/utils/utils.test.ts
import { describe, it, expect } from 'vitest'
import { formatBytes } from '@/lib/utils'

describe('formatBytes', () => {
  it('should format bytes correctly', () => {
    expect(formatBytes(1024)).toBe('1 KB')
  })
})
```

### Test Coverage Reports

Coverage reports are automatically generated and uploaded to [Codecov.io](https://codecov.io) on every PR:
- **Frontend:** `frontend/coverage/lcov.info`
- **Backend:** `backend/coverage.xml`
- **HTML Reports:** `htmlcov/` (backend), `coverage/` (frontend)

### Testing Best Practices

1. **Write tests first** (TDD approach) for new features
2. **Test edge cases** and error handling
3. **Keep tests isolated** - use fixtures and mocks
4. **Aim for high coverage** but focus on meaningful tests
5. **Run tests locally** before pushing to GitHub
6. **Use descriptive test names** that explain what is being tested

---

**Next:** [Troubleshooting](./07-troubleshooting.md)