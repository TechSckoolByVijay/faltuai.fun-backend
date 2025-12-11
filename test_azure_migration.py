#!/usr/bin/env python3
"""
Simple Azure PostgreSQL connection test and migration script
"""
import asyncio
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

import asyncpg

async def test_connection():
    """Test direct connection to Azure PostgreSQL"""
    try:
        # Connection details
        host = "faltuaidb.postgres.database.azure.com"
        port = 5432
        user = "dbadmin"
        password = "FaltuAIfun_p@55word"
        database = "faltuai_db"
        
        print("🔍 Testing direct connection to Azure PostgreSQL...")
        print(f"   Host: {host}")
        print(f"   Database: {database}")
        print(f"   User: {user}")
        
        # Try to connect
        conn = await asyncpg.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database,
            ssl='require'
        )
        
        print("✅ Successfully connected to Azure PostgreSQL!")
        
        # Test query
        version = await conn.fetchval('SELECT version()')
        print(f"   PostgreSQL Version: {version}")
        
        # Check if database exists and has tables
        tables = await conn.fetch("""
            SELECT tablename 
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print(f"   Existing tables: {len(tables)}")
        for table in tables:
            print(f"   - {table['tablename']}")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

async def run_alembic_migration():
    """Run Alembic migration using environment variables"""
    import subprocess
    
    try:
        print("\n🔄 Setting up environment variables...")
        
        # Set environment variables
        connection_string = "postgresql+asyncpg://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?ssl=require"
        os.environ["DATABASE_URL"] = connection_string
        os.environ["ASYNC_DATABASE_URL"] = connection_string
        
        print(f"   DATABASE_URL set")
        
        print("\n🔄 Checking Alembic status...")
        
        # Try to get current status first
        try:
            result = subprocess.run([
                sys.executable, "-m", "alembic", "current"
            ], capture_output=True, text=True, cwd=backend_dir)
            
            print(f"   Current status: {result.stdout.strip()}")
        except Exception as e:
            print(f"   Status check failed: {e}")
        
        # Check if we have migration files
        versions_dir = backend_dir / "alembic" / "versions"
        migration_files = list(versions_dir.glob("*.py")) if versions_dir.exists() else []
        
        if not migration_files:
            print("\n📝 Creating initial migration...")
            result = subprocess.run([
                sys.executable, "-m", "alembic", "revision", 
                "--autogenerate", "-m", "Initial migration"
            ], capture_output=True, text=True, cwd=backend_dir)
            
            if result.returncode != 0:
                print(f"❌ Migration creation failed: {result.stderr}")
                return False
            
            print("✅ Initial migration created")
        
        print("\n🚀 Applying migrations...")
        result = subprocess.run([
            sys.executable, "-m", "alembic", "upgrade", "head"
        ], capture_output=True, text=True, cwd=backend_dir)
        
        if result.returncode == 0:
            print("✅ Migrations applied successfully!")
            print(f"Migration output: {result.stdout}")
            return True
        else:
            print(f"❌ Migration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Migration process error: {e}")
        return False

async def verify_tables():
    """Verify that tables were created successfully"""
    try:
        print("\n🔍 Verifying table creation...")
        
        conn = await asyncpg.connect(
            host="faltuaidb.postgres.database.azure.com",
            port=5432,
            user="dbadmin",
            password="FaltuAIfun_p@55word",
            database="faltuai_db",
            ssl='require'
        )
        
        # Get table information
        tables = await conn.fetch("""
            SELECT 
                tablename,
                schemaname
            FROM pg_tables 
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        
        print(f"✅ Found {len(tables)} tables:")
        for table in tables:
            print(f"   - {table['tablename']}")
            
        # Check alembic version table
        try:
            version = await conn.fetchval("SELECT version_num FROM alembic_version")
            print(f"   Current Alembic version: {version}")
        except:
            print("   No Alembic version table found")
        
        await conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Verification failed: {e}")
        return False

async def main():
    """Main function"""
    print("🚀 Azure PostgreSQL Migration Script")
    print("=" * 40)
    
    # Step 1: Test connection
    if not await test_connection():
        print("\n❌ Cannot connect to database. Please check:")
        print("   - Network connectivity")
        print("   - Firewall rules")
        print("   - Credentials")
        print("   - SSL configuration")
        return
    
    # Step 2: Run migrations
    if not await run_alembic_migration():
        print("\n❌ Migration failed. Check the error messages above.")
        return
    
    # Step 3: Verify tables
    await verify_tables()
    
    print("\n🎉 Database migration completed successfully!")
    print("\nNext steps:")
    print("1. Update your Container App environment variables")
    print("2. Test your application endpoints")
    print("3. Set up monitoring and backups")

if __name__ == "__main__":
    asyncio.run(main())