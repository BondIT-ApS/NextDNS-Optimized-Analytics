#!/usr/bin/env python3
"""
🧱 E2E Test Data Seeder

Seeds the test database with realistic DNS log records for Playwright E2E tests.
Connects directly to PostgreSQL using the same env vars as the backend.

Requirements:
    pip install sqlalchemy psycopg2-binary

Usage:
    # Against docker-compose.test.yml
    POSTGRES_HOST=localhost POSTGRES_PORT=5434 \\
    POSTGRES_USER=nextdns_test POSTGRES_PASSWORD=nextdns_test \\
    POSTGRES_DB=nextdns_test python backend/tests/seed_e2e_data.py

    # Shorthand using defaults (matches docker-compose.test.yml)
    python backend/tests/seed_e2e_data.py

The script is idempotent — safe to run multiple times.
"""

import os
import sys
import json
import random
from datetime import datetime, timezone, timedelta

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5434")
POSTGRES_USER = os.getenv("POSTGRES_USER", "nextdns_test")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "nextdns_test")
POSTGRES_DB = os.getenv("POSTGRES_DB", "nextdns_test")

DATABASE_URL = (
    f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

TARGET_RECORDS = 1200  # enough for pagination testing

# ---------------------------------------------------------------------------
# Realistic test data pools
# ---------------------------------------------------------------------------

PROFILES = ["test-profile-1"]

DEVICES = [
    '{"name": "MacBook-Pro", "id": "device-1"}',
    '{"name": "iPhone-Martin", "id": "device-2"}',
    '{"name": "iPad-Home", "id": "device-3"}',
    '{"name": "Apple-TV", "id": "device-4"}',
    '{"name": "Smart-TV", "id": "device-5"}',
]

ALLOWED_DOMAINS = [
    ("api.github.com", "github.com"),
    ("avatars.githubusercontent.com", "githubusercontent.com"),
    ("www.google.com", "google.com"),
    ("fonts.googleapis.com", "googleapis.com"),
    ("accounts.google.com", "google.com"),
    ("mail.google.com", "google.com"),
    ("www.apple.com", "apple.com"),
    ("gateway.icloud.com", "icloud.com"),
    ("icloud.com", "icloud.com"),
    ("mesu.apple.com", "apple.com"),
    ("api.apple-cloudkit.com", "apple-cloudkit.com"),
    ("time.apple.com", "apple.com"),
    ("xp.apple.com", "apple.com"),
    ("www.reddit.com", "reddit.com"),
    ("api.reddit.com", "reddit.com"),
    ("www.youtube.com", "youtube.com"),
    ("i.ytimg.com", "ytimg.com"),
    ("s.youtube.com", "youtube.com"),
    ("www.netflix.com", "netflix.com"),
    ("api.netflix.com", "netflix.com"),
    ("www.amazon.com", "amazon.com"),
    ("api.amazon.com", "amazon.com"),
    ("www.cloudflare.com", "cloudflare.com"),
    ("cdn.cloudflare.com", "cloudflare.com"),
    ("www.stackoverflow.com", "stackoverflow.com"),
    ("cdn.jsdelivr.net", "jsdelivr.net"),
    ("raw.githubusercontent.com", "githubusercontent.com"),
    ("www.wikipedia.org", "wikipedia.org"),
    ("en.wikipedia.org", "wikipedia.org"),
    ("www.bbc.com", "bbc.com"),
    ("news.bbc.co.uk", "bbc.co.uk"),
    ("www.spotify.com", "spotify.com"),
    ("api.spotify.com", "spotify.com"),
    ("open.spotify.com", "spotify.com"),
    ("www.twitter.com", "twitter.com"),
    ("api.twitter.com", "twitter.com"),
    ("www.linkedin.com", "linkedin.com"),
    ("api.linkedin.com", "linkedin.com"),
    ("www.dropbox.com", "dropbox.com"),
    ("www.slack.com", "slack.com"),
    ("slack-msgs.com", "slack-msgs.com"),
]

BLOCKED_DOMAINS = [
    ("ads.google.com", "google.com"),
    ("googleads.g.doubleclick.net", "doubleclick.net"),
    ("ad.doubleclick.net", "doubleclick.net"),
    ("pagead2.googlesyndication.com", "googlesyndication.com"),
    ("stats.g.doubleclick.net", "doubleclick.net"),
    ("www.googletagmanager.com", "googletagmanager.com"),
    ("analytics.google.com", "google.com"),
    ("tracking.example.com", "example.com"),
    ("ads.facebook.com", "facebook.com"),
    ("pixel.facebook.com", "facebook.com"),
    ("connect.facebook.net", "facebook.net"),
    ("www.facebook.com", "facebook.com"),
    ("graph.facebook.com", "facebook.com"),
    ("ads.twitter.com", "twitter.com"),
    ("analytics.twitter.com", "twitter.com"),
    ("t.co", "t.co"),
    ("ads.linkedin.com", "linkedin.com"),
    ("px.ads.linkedin.com", "linkedin.com"),
    ("track.customer.io", "customer.io"),
    ("api.segment.io", "segment.io"),
    ("cdn.segment.com", "segment.com"),
    ("api.mixpanel.com", "mixpanel.com"),
    ("cdn.mxpnl.com", "mxpnl.com"),
    ("beacon.krxd.net", "krxd.net"),
    ("geo.yahoo.com", "yahoo.com"),
    ("s.yimg.com", "yimg.com"),
    ("ads.yahoo.com", "yahoo.com"),
    ("ads.pubmatic.com", "pubmatic.com"),
    ("simage2.pubmatic.com", "pubmatic.com"),
    ("ib.adnxs.com", "adnxs.com"),
    ("secure.adnxs.com", "adnxs.com"),
    ("cdn.taboola.com", "taboola.com"),
    ("trc.taboola.com", "taboola.com"),
    ("ad.taboola.com", "taboola.com"),
    ("engine.carbonads.com", "carbonads.com"),
    ("srv.carbonads.net", "carbonads.net"),
    ("metrics.apple.com", "apple.com"),
    ("telemetry.microsoft.com", "microsoft.com"),
    ("vortex.data.microsoft.com", "microsoft.com"),
    ("settings-win.data.microsoft.com", "microsoft.com"),
]


# ---------------------------------------------------------------------------
# Seeder logic
# ---------------------------------------------------------------------------


def build_db_url() -> str:
    return DATABASE_URL


def create_records(n: int) -> list[dict]:
    """Generate n realistic DNS log records spread over the last 30 days."""
    now = datetime.now(timezone.utc)
    records = []

    for i in range(n):
        # Distribute timestamps over last 30 days, denser toward recent
        age_seconds = random.randint(0, 30 * 24 * 3600)
        ts = now - timedelta(seconds=age_seconds)

        # ~30% of queries are blocked
        blocked = random.random() < 0.30
        pool = BLOCKED_DOMAINS if blocked else ALLOWED_DOMAINS
        domain, tld = random.choice(pool)

        profile_id = random.choice(PROFILES)
        device_json = random.choice(DEVICES)

        records.append(
            {
                "timestamp": ts,
                "domain": domain,
                "tld": tld,
                "blocked": blocked,
                "profile_id": profile_id,
                "device": device_json,
                "data": json.dumps({"dnssec": False, "protocol": "Do53"}),
            }
        )

    return records


def seed(engine) -> None:
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # Count existing records to avoid re-seeding
        existing = session.execute(
            text("SELECT COUNT(*) FROM dns_logs WHERE profile_id = 'test-profile-1'")
        ).scalar()

        if existing and existing >= TARGET_RECORDS:
            print(
                f"✅ Already have {existing} records for test-profile-1, skipping seed."
            )
            return

        print(f"🌱 Seeding {TARGET_RECORDS} DNS log records...")

        records = create_records(TARGET_RECORDS)

        # Bulk insert using parameterised query (avoids ORM overhead)
        session.execute(
            text(
                """
                INSERT INTO dns_logs (timestamp, domain, tld, blocked, profile_id, device, data)
                VALUES (:timestamp, :domain, :tld, :blocked, :profile_id, :device, :data)
                ON CONFLICT (timestamp, domain, profile_id, device) DO NOTHING
                """
            ),
            records,
        )
        session.commit()

        final_count = session.execute(
            text("SELECT COUNT(*) FROM dns_logs WHERE profile_id = 'test-profile-1'")
        ).scalar()

        print(f"✅ Seeded successfully. Total records for test-profile-1: {final_count}")

    except Exception as exc:
        session.rollback()
        print(f"❌ Seed failed: {exc}", file=sys.stderr)
        sys.exit(1)
    finally:
        session.close()


def main() -> None:
    print(f"🔗 Connecting to {POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}...")
    engine = create_engine(build_db_url(), pool_pre_ping=True)

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print("✅ Database connection OK")
    except Exception as exc:
        print(f"❌ Cannot connect to database: {exc}", file=sys.stderr)
        sys.exit(1)

    seed(engine)


if __name__ == "__main__":
    main()
