# 🧱 Scripts Directory

This directory contains utility scripts for the NextDNS Optimized Analytics project.

## 📋 Available Scripts

### Database Migration

#### `migrate-to-new-db.sh`
Batched database migration script for transferring data from a source database to a target database.

**Features:**
- Migrates data in configurable batches (default: 5000 records) to avoid performance issues
- Supports multiple migration modes: all data, specific date, date range, last 7/30 days
- Handles duplicate records gracefully using `ON CONFLICT` clauses
- Optional truncate before migration with confirmation prompt
- Progress tracking and verification after completion

**Usage:**
```bash
# Set environment variables (see .env.migration.template)
source .env.migration

# Interactive mode - will prompt for options
./migrate-to-new-db.sh

# Migrate specific date
./migrate-to-new-db.sh --date 2025-12-15

# Migrate date range
./migrate-to-new-db.sh --start 2025-12-15 --end 2025-12-20
```

**Required Environment Variables:**
- `SOURCE_DB_PASSWORD` - Source database password
- `TARGET_DB_HOST` - Target database host
- `TARGET_DB_USER` - Target database user
- `TARGET_DB_NAME` - Target database name
- `TARGET_DB_PASSWORD` - Target database password

See `.env.migration.template` for all available environment variables.

#### `.env.migration.template`
Template file for database migration environment variables.

**Usage:**
1. Copy this file to `.env.migration`
2. Fill in your actual database credentials
3. Source the file before running migration: `source .env.migration`

**Note:** `.env.migration` is in `.gitignore` to prevent committing credentials.

#### `.env.migration`
Your actual environment variables file with real credentials (not tracked in git).

### Testing Scripts

#### `test_1000_dns_queries.sh`
Generates and sends 1000 test DNS query logs to the API for testing purposes.

**Usage:**
```bash
./test_1000_dns_queries.sh
```

#### `test_rate_limiting.sh`
Tests the API rate limiting functionality by sending requests at various rates.

**Features:**
- Tests different rate limiting scenarios
- Validates rate limit headers and responses
- Useful for ensuring rate limiting is working correctly

**Usage:**
```bash
./test_rate_limiting.sh
```

## 🔒 Security Notes

- Never commit `.env.migration` or any file containing real credentials
- Always use `.env.migration.template` as a reference for required variables
- The `.gitignore` is configured to exclude credential files automatically

## 🧱 LEGO Philosophy

Like building with LEGO blocks, these scripts are modular and reusable:
- Each script handles a specific task
- Environment configuration is separated from logic
- Scripts can be combined for complex workflows
