"""
Debug script to check database connection and schema from Container App perspective
"""
from fastapi import APIRouter, HTTPException
from app.core.database import engine
from sqlalchemy import text

debug_router = APIRouter(prefix="/debug", tags=["debug"])

@debug_router.get("/db-schema")
async def check_database_schema():
    """Check what database schema the app is actually seeing"""
    try:
        async with engine.begin() as conn:
            # Check if tables exist
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result]
            
            schema_info = {"tables": tables}
            
            # Check resume_roast_sessions columns if table exists
            if 'resume_roast_sessions' in tables:
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'resume_roast_sessions' 
                    ORDER BY ordinal_position
                """))
                schema_info["resume_roast_sessions_columns"] = [
                    {"name": row[0], "type": row[1]} for row in result
                ]
            
            # Check users columns if table exists
            if 'users' in tables:
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    ORDER BY ordinal_position
                """))
                schema_info["users_columns"] = [
                    {"name": row[0], "type": row[1]} for row in result
                ]
            
            # Get database connection info
            result = await conn.execute(text("SELECT current_database(), current_user"))
            db_info = result.fetchone()
            schema_info["database"] = db_info[0]
            schema_info["user"] = db_info[1]
            
            return schema_info
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")