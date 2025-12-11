"""
Fix Azure PostgreSQL database schema to match our models
"""
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

# Azure database URL
AZURE_URL = 'postgresql+asyncpg://dbadmin:FaltuAIfun_p%4055word@faltuaidb.postgres.database.azure.com:5432/faltuai_db?ssl=require'

async def fix_database_schema():
    """Fix the database schema to match our models"""
    engine = create_async_engine(AZURE_URL)
    
    try:
        async with engine.begin() as conn:
            print("🔧 Fixing Azure PostgreSQL database schema...")
            
            # Check current schema
            result = await conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """))
            current_columns = [row[0] for row in result]
            print("Current columns:", current_columns)
            
            # Rename 'name' to 'full_name' if it exists
            if 'name' in current_columns and 'full_name' not in current_columns:
                await conn.execute(text("ALTER TABLE users RENAME COLUMN name TO full_name;"))
                print("✅ Renamed 'name' column to 'full_name'")
            
            # Add missing columns if they don't exist
            missing_columns = {
                'avatar_url': 'TEXT',
                'is_premium': 'BOOLEAN DEFAULT FALSE NOT NULL'
            }
            
            for column, column_type in missing_columns.items():
                if column not in current_columns:
                    await conn.execute(text(f"ALTER TABLE users ADD COLUMN {column} {column_type};"))
                    print(f"✅ Added column '{column}' ({column_type})")
            
            # Verify final schema
            result = await conn.execute(text("""
                SELECT column_name, data_type, is_nullable 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position;
            """))
            
            print("\n📋 Final users table schema:")
            for row in result:
                print(f"  {row[0]}: {row[1]} (nullable: {row[2]})")
            
            print("\n🎉 Database schema fixed successfully!")
            
    except Exception as e:
        print(f"❌ Error fixing database schema: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(fix_database_schema())