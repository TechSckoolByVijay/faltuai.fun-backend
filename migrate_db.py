#!/usr/bin/env python3
"""
Database migration script for FaltuAI application
Run this script to initialize the database schema and create initial migration
"""
import asyncio
import os
import sys
import subprocess
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.core.database import init_db, engine, Base
from app.models import *  # Import all models

async def create_initial_migration():
    """Create initial Alembic migration"""
    print("🔄 Creating initial Alembic migration...")
    
    try:
        # Change to backend directory
        os.chdir(backend_dir)
        
        # Check if alembic is initialized
        if not Path("alembic.ini").exists():
            print("❌ Alembic not configured. Please check alembic.ini file.")
            return False
            
        # Create initial migration
        result = subprocess.run([
            "alembic", "revision", "--autogenerate", 
            "-m", "Initial migration with users and resume_roast tables"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Initial migration created successfully")
            print(f"Migration output: {result.stdout}")
            return True
        else:
            print(f"❌ Migration creation failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error creating migration: {e}")
        return False

async def run_migrations():
    """Run database migrations"""
    print("🔄 Running database migrations...")
    
    try:
        os.chdir(backend_dir)
        
        # Run migrations
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Migrations completed successfully")
            print(f"Migration output: {result.stdout}")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error running migrations: {e}")
        return False

async def initialize_database():
    """Initialize database tables directly (fallback)"""
    print("🔄 Initializing database tables...")
    
    try:
        await init_db()
        print("✅ Database tables created successfully")
        return True
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False

async def main():
    """Main migration function"""
    print("🚀 Starting FaltuAI database setup...")
    
    # Try to create migration first
    migration_created = await create_initial_migration()
    
    if migration_created:
        # Run the migrations
        migration_success = await run_migrations()
        if migration_success:
            print("🎉 Database setup completed with migrations!")
            return
    
    # Fallback to direct table creation
    print("📄 Falling back to direct table creation...")
    direct_success = await initialize_database()
    
    if direct_success:
        print("🎉 Database setup completed with direct table creation!")
    else:
        print("❌ Database setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())