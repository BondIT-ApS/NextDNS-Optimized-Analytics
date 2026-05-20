## Overview

<!-- Brief description of what changed and why. Link to related issue(s). -->

Closes #

## Changes

### Added
-

### Modified
-

### Removed
-

## How to Test

<!-- Steps to verify the changes work correctly. -->

1.
2.
3.

## Quality Checklist

### General
- [ ] Branch is up to date with `main`
- [ ] Conventional commit messages used (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`)
- [ ] Documentation updated in `/docs/` (if applicable)

### Frontend (if changed)
- [ ] `npm run lint` passes
- [ ] `npm run type-check` passes
- [ ] `npm run format:check` passes
- [ ] `npm run test -- --run` passes
- [ ] `npm audit --audit-level=moderate` clean

### Backend (if changed)
- [ ] `black . --check` passes
- [ ] `pylint . --rcfile=../.pylintrc` passes
- [ ] `pytest tests/ -v` passes
- [ ] `bandit -r . -x ./tests/ -x ./venv/ --skip B101` clean

### Docker (if applicable)
- [ ] `docker-compose up -d --build` succeeds
- [ ] Health endpoints respond (`/health`, `/health/detailed`)

### Workflows (if changed)
- [ ] `actionlint .github/workflows/*.yml` passes
