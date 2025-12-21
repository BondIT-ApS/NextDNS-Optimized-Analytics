#!/bin/bash
# Batched migration script to transfer data from source DB to target DB
# This script migrates data in batches to avoid performance issues with large datasets
#
# Required Environment Variables:
#   SOURCE_DB_PASSWORD - Source database password (required)
#   TARGET_DB_HOST     - Target database host (required)
#   TARGET_DB_USER     - Target database user (required)
#   TARGET_DB_NAME     - Target database name (required)
#   TARGET_DB_PASSWORD - Target database password (required)
#
# Optional Environment Variables:
#   SOURCE_DB_HOST     - Source database host (default: localhost)
#   SOURCE_DB_PORT     - Source database port (default: 5432)
#   SOURCE_DB_USER     - Source database user (default: postgres)
#   SOURCE_DB_NAME     - Source database name (default: nextdns)
#   TARGET_DB_PORT     - Target database port (default: 5432)
#
# Usage:
#   ./migrate-to-new-db.sh                    # Interactive mode
#   ./migrate-to-new-db.sh --date 2025-12-05  # Migrate specific date
#   ./migrate-to-new-db.sh --start 2025-12-01 --end 2025-12-05  # Migrate date range

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BATCH_SIZE=5000  # Number of records per batch (increased for better performance)

# Source DB (Local) - Set these environment variables before running
SOURCE_HOST="${SOURCE_DB_HOST:-localhost}"
SOURCE_PORT="${SOURCE_DB_PORT:-5432}"
SOURCE_USER="${SOURCE_DB_USER:-postgres}"
SOURCE_DB="${SOURCE_DB_NAME:-nextdns}"
SOURCE_PASSWORD="${SOURCE_DB_PASSWORD}"

# Target DB (Production) - Set these environment variables before running
TARGET_HOST="${TARGET_DB_HOST}"
TARGET_PORT="${TARGET_DB_PORT:-5432}"
TARGET_USER="${TARGET_DB_USER}"
TARGET_DB="${TARGET_DB_NAME}"
TARGET_PASSWORD="${TARGET_DB_PASSWORD}"

# Validate required environment variables
MISSING_VARS=()
if [ -z "$SOURCE_PASSWORD" ]; then MISSING_VARS+=("SOURCE_DB_PASSWORD"); fi
if [ -z "$TARGET_HOST" ]; then MISSING_VARS+=("TARGET_DB_HOST"); fi
if [ -z "$TARGET_USER" ]; then MISSING_VARS+=("TARGET_DB_USER"); fi
if [ -z "$TARGET_DB" ]; then MISSING_VARS+=("TARGET_DB_NAME"); fi
if [ -z "$TARGET_PASSWORD" ]; then MISSING_VARS+=("TARGET_DB_PASSWORD"); fi

if [ ${#MISSING_VARS[@]} -gt 0 ]; then
    echo -e "${RED}❌ Error: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "${RED}   - $var${NC}"
    done
    echo ""
    echo -e "${YELLOW}Please set the required environment variables before running this script.${NC}"
    echo -e "${YELLOW}See script header for documentation.${NC}"
    exit 1
fi

# Parse command-line arguments
MIGRATE_DATE=""
START_DATE=""
END_DATE=""
MIGRATE_MODE="interactive"

while [[ $# -gt 0 ]]; do
    case $1 in
        --date)
            MIGRATE_DATE="$2"
            MIGRATE_MODE="single_date"
            shift 2
            ;;
        --start)
            START_DATE="$2"
            MIGRATE_MODE="date_range"
            shift 2
            ;;
        --end)
            END_DATE="$2"
            shift 2
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Usage: $0 [--date YYYY-MM-DD] [--start YYYY-MM-DD --end YYYY-MM-DD]"
            exit 1
            ;;
    esac
done

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🧱 NextDNS Analytics - Database Migration Tool${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📦 Batch size: $BATCH_SIZE records${NC}"
echo ""

# Interactive mode - ask for migration options
if [ "$MIGRATE_MODE" = "interactive" ]; then
    echo -e "${BLUE}What would you like to migrate?${NC}"
    echo "  1) All data (full database)"
    echo "  2) Last 7 days"
    echo "  3) Last 30 days"
    echo "  4) Specific date"
    echo "  5) Custom date range"
    echo ""
    read -p "Enter your choice (1-5): " CHOICE
    
    case $CHOICE in
        1)
            MIGRATE_MODE="all"
            ;;
        2)
            MIGRATE_MODE="last_7_days"
            START_DATE=$(date -u -v-7d +"%Y-%m-%d")
            END_DATE=$(date -u +"%Y-%m-%d")
            ;;
        3)
            MIGRATE_MODE="last_30_days"
            START_DATE=$(date -u -v-30d +"%Y-%m-%d")
            END_DATE=$(date -u +"%Y-%m-%d")
            ;;
        4)
            read -p "Enter date (YYYY-MM-DD): " MIGRATE_DATE
            MIGRATE_MODE="single_date"
            ;;
        5)
            read -p "Enter start date (YYYY-MM-DD): " START_DATE
            read -p "Enter end date (YYYY-MM-DD): " END_DATE
            MIGRATE_MODE="date_range"
            ;;
        *)
            echo -e "${RED}❌ Invalid choice${NC}"
            exit 1
            ;;
    esac
    echo ""
fi

# Ask if user wants to truncate tables first
echo -e "${YELLOW}⚠️  Do you want to TRUNCATE the destination database before migration?${NC}"
echo -e "${YELLOW}    This will DELETE ALL existing data in the production database!${NC}"
read -p "Truncate tables? (yes/no) [no]: " TRUNCATE_CHOICE
TRUNCATE_CHOICE=${TRUNCATE_CHOICE:-no}
echo ""

if [ "$TRUNCATE_CHOICE" = "yes" ]; then
    echo -e "${YELLOW}🔄 Truncating existing data in production tables...${NC}"
    PGPASSWORD=$TARGET_PASSWORD psql -h $TARGET_HOST -p $TARGET_PORT -U $TARGET_USER -d $TARGET_DB --set=sslmode=require << EOF
TRUNCATE TABLE dns_logs CASCADE;
TRUNCATE TABLE fetch_status CASCADE;
EOF
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tables truncated successfully${NC}"
    else
        echo -e "${RED}❌ Failed to truncate tables${NC}"
        exit 1
    fi
else
    echo -e "${BLUE}➡️  Skipping truncate - will append to existing data${NC}"
fi
echo ""

# Step 2: Build WHERE clause based on migration mode and count records
echo -e "${YELLOW}🔄 Step 2: Counting records in source database...${NC}"

WHERE_CLAUSE=""
case $MIGRATE_MODE in
    "all")
        WHERE_CLAUSE="1=1"  # No filter - all records
        echo -e "${BLUE}🔍 Migration mode: ALL DATA${NC}"
        ;;
    "single_date"|4)
        WHERE_CLAUSE="DATE(timestamp) = '$MIGRATE_DATE'"
        echo -e "${BLUE}🔍 Migration mode: SINGLE DATE ($MIGRATE_DATE)${NC}"
        ;;
    "date_range"|"last_7_days"|"last_30_days"|5)
        WHERE_CLAUSE="DATE(timestamp) >= '$START_DATE' AND DATE(timestamp) <= '$END_DATE'"
        echo -e "${BLUE}🔍 Migration mode: DATE RANGE ($START_DATE to $END_DATE)${NC}"
        ;;
esac

TOTAL_RECORDS=$(PGPASSWORD=$SOURCE_PASSWORD psql -h $SOURCE_HOST -p $SOURCE_PORT -U $SOURCE_USER -d $SOURCE_DB -t -c "SELECT COUNT(*) FROM dns_logs WHERE $WHERE_CLAUSE;" | xargs)
echo -e "${GREEN}📊 Total records to migrate: $TOTAL_RECORDS${NC}"
echo ""

if [ "$TOTAL_RECORDS" -eq 0 ]; then
    echo -e "${YELLOW}⚠️  No records to migrate${NC}"
    exit 0
fi

# Step 3: Migrate dns_logs in batches
echo -e "${YELLOW}🔄 Step 3: Migrating dns_logs table in batches...${NC}"
OFFSET=0
MIGRATED=0

while [ $OFFSET -lt $TOTAL_RECORDS ]; do
    RECORDS_REMAINING=$((TOTAL_RECORDS - OFFSET))
    CURRENT_BATCH=$((RECORDS_REMAINING < BATCH_SIZE ? RECORDS_REMAINING : BATCH_SIZE))
    echo -e "  Migrating records $OFFSET to $((OFFSET + CURRENT_BATCH))..."
    
    # Dump batch from source to temporary file with proper CSV formatting
    TEMP_FILE=$(mktemp)
    PGPASSWORD=$SOURCE_PASSWORD psql -h $SOURCE_HOST -p $SOURCE_PORT -U $SOURCE_USER -d $SOURCE_DB -c "\\copy (SELECT timestamp, domain, action, device, client_ip, query_type, blocked, profile_id, tld, data, created_at FROM dns_logs WHERE $WHERE_CLAUSE ORDER BY timestamp LIMIT $BATCH_SIZE OFFSET $OFFSET) TO STDOUT WITH (FORMAT CSV, HEADER false, QUOTE '\"', ESCAPE '\"', FORCE_QUOTE *)" > "$TEMP_FILE"
    
    # Check if temp file has data
    if [ ! -s "$TEMP_FILE" ]; then
        echo -e "${YELLOW}  ⚠️  No more data to migrate${NC}"
        rm -f "$TEMP_FILE"
        break
    fi
    
    # Load batch into target using a temporary table to handle duplicates
    PGPASSWORD=$TARGET_PASSWORD psql -h $TARGET_HOST -p $TARGET_PORT -U $TARGET_USER -d $TARGET_DB --set=sslmode=require << EOF
-- Create temporary table
CREATE TEMP TABLE temp_dns_logs (
    timestamp TIMESTAMPTZ,
    domain TEXT,
    action TEXT,
    device TEXT,
    client_ip TEXT,
    query_type TEXT,
    blocked BOOLEAN,
    profile_id TEXT,
    tld TEXT,
    data JSONB,
    created_at TIMESTAMPTZ
);

-- Copy data into temp table
\\copy temp_dns_logs (timestamp, domain, action, device, client_ip, query_type, blocked, profile_id, tld, data, created_at) FROM '$TEMP_FILE' WITH (FORMAT CSV, HEADER false, QUOTE '"', ESCAPE '"')

-- Insert with conflict handling
INSERT INTO dns_logs (timestamp, domain, action, device, client_ip, query_type, blocked, profile_id, tld, data, created_at)
SELECT timestamp, domain, action, device, client_ip, query_type, blocked, profile_id, tld, data, created_at
FROM temp_dns_logs
ON CONFLICT (timestamp, domain, client_ip) DO NOTHING;

-- Drop temp table
DROP TABLE temp_dns_logs;
EOF
    
    COPY_EXIT_CODE=$?
    # Clean up temporary file
    rm -f "$TEMP_FILE"
    
    if [ $COPY_EXIT_CODE -eq 0 ]; then
        MIGRATED=$((MIGRATED + CURRENT_BATCH))
        PROGRESS=$((OFFSET * 100 / TOTAL_RECORDS))
        echo -e "${GREEN}  ✅ Progress: $((OFFSET + CURRENT_BATCH))/$TOTAL_RECORDS ($PROGRESS%)${NC}"
    else
        echo -e "${RED}  ❌ Failed to migrate batch at offset $OFFSET${NC}"
        echo -e "${RED}     Check the error message above for details${NC}"
        exit 1
    fi
    
    OFFSET=$((OFFSET + BATCH_SIZE))
done

echo -e "${GREEN}✅ dns_logs migration complete!${NC}"
echo ""

# Step 4: Migrate fetch_status table (small table, no batching needed)
echo -e "${YELLOW}🔄 Step 4: Migrating fetch_status table...${NC}"

# Dump fetch_status data to temporary file
FETCH_STATUS_FILE=$(mktemp)
PGPASSWORD=$SOURCE_PASSWORD psql -h $SOURCE_HOST -p $SOURCE_PORT -U $SOURCE_USER -d $SOURCE_DB -c "\\copy (SELECT profile_id, last_fetched_timestamp, last_fetch_status, records_fetched FROM fetch_status) TO STDOUT WITH (FORMAT CSV, HEADER false, QUOTE '\"', ESCAPE '\"', FORCE_QUOTE *)" > "$FETCH_STATUS_FILE"

# Load into target with conflict handling
PGPASSWORD=$TARGET_PASSWORD psql -h $TARGET_HOST -p $TARGET_PORT -U $TARGET_USER -d $TARGET_DB --set=sslmode=require << EOF
-- Create temporary table
CREATE TEMP TABLE temp_fetch_status (
    profile_id TEXT,
    last_fetched_timestamp TIMESTAMPTZ,
    last_fetch_status TEXT,
    records_fetched INTEGER
);

-- Copy data into temp table
\\copy temp_fetch_status (profile_id, last_fetched_timestamp, last_fetch_status, records_fetched) FROM '$FETCH_STATUS_FILE' WITH (FORMAT CSV, HEADER false, QUOTE '"', ESCAPE '"')

-- Insert with conflict handling (update if exists)
INSERT INTO fetch_status (profile_id, last_fetched_timestamp, last_fetch_status, records_fetched)
SELECT profile_id, last_fetched_timestamp, last_fetch_status, records_fetched
FROM temp_fetch_status
ON CONFLICT (profile_id) 
DO UPDATE SET 
    last_fetched_timestamp = EXCLUDED.last_fetched_timestamp,
    last_fetch_status = EXCLUDED.last_fetch_status,
    records_fetched = EXCLUDED.records_fetched;

-- Drop temp table
DROP TABLE temp_fetch_status;
EOF

FETCH_EXIT_CODE=$?
rm -f "$FETCH_STATUS_FILE"

if [ $FETCH_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✅ fetch_status migration complete!${NC}"
else
    echo -e "${RED}❌ fetch_status migration failed${NC}"
    exit 1
fi
echo ""

# Step 5: Verify migration
echo -e "${YELLOW}🔄 Step 5: Verifying migration...${NC}"

if [ "$MIGRATE_MODE" = "all" ]; then
    VERIFY_QUERY="SELECT COUNT(*) FROM dns_logs"
else
    VERIFY_QUERY="SELECT COUNT(*) FROM dns_logs WHERE $WHERE_CLAUSE"
fi

TARGET_RECORD_COUNT=$(PGPASSWORD=$TARGET_PASSWORD psql -h $TARGET_HOST -p $TARGET_PORT -U $TARGET_USER -d $TARGET_DB --set=sslmode=require -t -c "$VERIFY_QUERY;" | xargs)

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  📊 Migration Summary${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "   Source records (to migrate): ${YELLOW}$TOTAL_RECORDS${NC}"
echo -e "   Target records (migrated):    ${GREEN}$MIGRATED${NC}"
echo -e "   Target records (in range):    ${GREEN}$TARGET_RECORD_COUNT${NC}"

if [ "$TOTAL_RECORDS" -eq "$TARGET_RECORD_COUNT" ] || [ "$TRUNCATE_CHOICE" != "yes" ]; then
    echo -e "${GREEN}✅ Migration complete!${NC}"
else
    echo -e "${YELLOW}⚠️  Record count mismatch - some records may have been skipped (duplicates?)${NC}"
fi

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🎉 All done! Your DigitalOcean database migration is complete.${NC}"
