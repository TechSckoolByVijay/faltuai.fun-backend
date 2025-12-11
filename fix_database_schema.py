"""
Fix database schema issues by recreating tables
"""
import asyncio
from app.core.database import engine, Base
from app.models.user import User
from app.models.resume_roast import ResumeRoastSession, UserActivityLog

async def fix_database_schema():
    """Recreate tables to fix schema issues"""
    print("Fixing database schema...")
    
    async with engine.begin() as conn:
        # Drop and recreate tables to ensure schema consistency
        print("Dropping existing tables...")
        await conn.run_sync(Base.metadata.drop_all)
        
        print("Creating fresh tables...")
        await conn.run_sync(Base.metadata.create_all)
        
        print("Database schema fixed successfully!")

if __name__ == "__main__":
    asyncio.run(fix_database_schema())