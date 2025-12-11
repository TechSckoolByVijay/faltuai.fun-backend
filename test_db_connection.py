#!/usr/bin/env python3
"""
Test script to verify database connectivity issues
"""
import asyncio
import os
import asyncpg

async def test_database_connection():
    """Test the database connection directly"""
    
    # The connection string from your deployment
    connection_string = "postgresql://dbadmin:FaltuAIfun_p@55word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?sslmode=require"
    
    print("🔍 Testing database connectivity...")
    print(f"Connection string: {connection_string}")
    
    try:
        # Test asyncpg connection (what your app uses)
        print("\n📡 Testing asyncpg connection...")
        conn = await asyncpg.connect(connection_string.replace("?sslmode=require", "?ssl=require"))
        
        # Test simple query
        result = await conn.fetchval("SELECT 1")
        print(f"✅ asyncpg connection successful: {result}")
        
        # Test if tables exist
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """)
        
        print(f"📋 Found {len(tables)} tables:")
        for table in tables:
            print(f"   • {table['table_name']}")
        
        await conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_database_connection())
    if success:
        print("\n🎉 Database connectivity test PASSED!")
    else:
        print("\n💥 Database connectivity test FAILED!")