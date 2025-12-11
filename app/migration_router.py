"""
Migration endpoint to fix database schema from within Container App
"""
from fastapi import APIRouter, HTTPException
from app.core.database import engine, Base
from sqlalchemy import text

migration_router = APIRouter(prefix="/migration", tags=["migration"])

@migration_router.post("/recreate-schema")
async def recreate_database_schema():
    """Recreate database schema to match current models"""
    try:
        async with engine.begin() as conn:
            # Drop existing tables
            await conn.execute(text("DROP TABLE IF EXISTS resume_roast_sessions CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS user_activity_logs CASCADE"))
            await conn.execute(text("DROP TABLE IF EXISTS system_metrics CASCADE"))
            
            # Recreate tables with correct schema
            await conn.run_sync(Base.metadata.create_all)
            
            return {
                "status": "success", 
                "message": "Database schema recreated successfully",
                "action": "All tables dropped and recreated with current model definitions"
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Migration failed: {str(e)}")

@migration_router.get("/check-schema")
async def check_current_schema():
    """Check current schema before migration"""
    try:
        async with engine.begin() as conn:
            # Get table info
            result = await conn.execute(text("""
                SELECT table_name, column_name, data_type 
                FROM information_schema.columns 
                WHERE table_schema = 'public' 
                AND table_name IN ('users', 'resume_roast_sessions', 'user_activity_logs')
                ORDER BY table_name, ordinal_position
            """))
            
            schema = {}
            for row in result:
                table_name, column_name, data_type = row
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({"column": column_name, "type": data_type})
            
            return {"current_schema": schema}
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Schema check failed: {str(e)}")