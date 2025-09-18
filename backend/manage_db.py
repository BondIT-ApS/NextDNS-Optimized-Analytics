#!/usr/bin/env python3
"""
Database management script for NextDNS Optimized Analytics

This script provides easy commands for managing database migrations using Alembic.
Like having a LEGO instruction manual for your database schema!

Migration files follow the pattern: YYYY_MM_DD_<revision_id>_<description>.py
Example: 2025_09_18_5eef40b793b3_initial_postgresql_schema_with_enhanced_dns_logs.py

Usage:
    python manage_db.py init     # Initialize database with current schema
    python manage_db.py upgrade  # Upgrade to latest schema version
    python manage_db.py status   # Show current migration status
    python manage_db.py history  # Show migration history

Note: Make sure PostgreSQL is running and environment variables are set!
"""

import os
import sys
import subprocess
from pathlib import Path

def run_alembic_command(command_args):
    """Run an Alembic command with proper error handling."""
    try:
        cmd = ['alembic'] + command_args
        print(f"🧱 Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd=Path(__file__).parent, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print(f"⚠️ Warnings: {result.stderr}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Alembic command: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

def check_environment():
    """Check if required environment variables are set."""
    # Database connection variables (required for migrations)
    db_vars = ['POSTGRES_USER', 'POSTGRES_PASSWORD', 'POSTGRES_DB', 'POSTGRES_HOST']
    # NextDNS API variables (optional for migrations, but needed for the app to work)
    api_vars = ['API_KEY', 'PROFILE_ID', 'LOCAL_API_KEY']
    
    missing_db_vars = []
    missing_api_vars = []
    
    for var in db_vars:
        if not os.getenv(var):
            missing_db_vars.append(var)
    
    for var in api_vars:
        if not os.getenv(var):
            missing_api_vars.append(var)
    
    if missing_db_vars:
        print(f"❌ Missing required database variables: {', '.join(missing_db_vars)}")
        print("💡 Make sure to set these variables or load your .env file")
        return False
    
    if missing_api_vars:
        print(f"⚠️  Missing NextDNS API variables: {', '.join(missing_api_vars)}")
        print("💡 These are needed for the application to fetch NextDNS logs")
        print("🧱 Database migrations will work, but the app won't fetch logs")
    
    print("✅ Database environment variables are properly configured")
    if not missing_api_vars:
        print("✅ NextDNS API environment variables are properly configured")
    
    return True

def init_database():
    """Initialize the database with the latest schema."""
    print("🏗️ Initializing database schema...")
    if not check_environment():
        return False
    
    return run_alembic_command(['upgrade', 'head'])

def upgrade_database():
    """Upgrade database to the latest schema."""
    print("⬆️ Upgrading database schema...")
    if not check_environment():
        return False
    
    return run_alembic_command(['upgrade', 'head'])

def show_status():
    """Show current migration status."""
    print("📊 Checking migration status...")
    if not check_environment():
        return False
    
    return run_alembic_command(['current'])

def show_history():
    """Show migration history."""
    print("📜 Migration history:")
    return run_alembic_command(['history'])

def main():
    """Main CLI interface."""
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    commands = {
        'init': init_database,
        'upgrade': upgrade_database,
        'status': show_status,
        'history': show_history,
    }
    
    if command not in commands:
        print(f"❌ Unknown command: {command}")
        print(__doc__)
        sys.exit(1)
    
    print("🧱 NextDNS Optimized Analytics - Database Management")
    print("=" * 50)
    
    success = commands[command]()
    
    if success:
        print("✅ Command completed successfully!")
    else:
        print("❌ Command failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()