"""
Database configuration module for SQLAlchemy with PostgreSQL
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from typing import AsyncGenerator

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://faltuai_user:faltuai_password@localhost:5432/faltuai_db")

# Use explicit ASYNC_DATABASE_URL if provided, otherwise convert from DATABASE_URL
ASYNC_DATABASE_URL = os.getenv("ASYNC_DATABASE_URL")
if not ASYNC_DATABASE_URL:
    # Convert to async URL if needed and fix SSL parameters for asyncpg
    if DATABASE_URL.startswith("postgresql://"):
        ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://")
        # Fix SSL parameter for asyncpg
        ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("sslmode=require", "ssl=require")
    else:
        ASYNC_DATABASE_URL = DATABASE_URL
        # Fix SSL parameter for asyncpg if present
        if "sslmode=require" in ASYNC_DATABASE_URL:
            ASYNC_DATABASE_URL = ASYNC_DATABASE_URL.replace("sslmode=require", "ssl=require")

# SQLAlchemy async engine
engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=bool(os.getenv("DEBUG", False)),  # Log SQL queries in debug mode
    pool_pre_ping=True,
    pool_recycle=3600,
)

# Async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
metadata = MetaData()
Base = declarative_base(metadata=metadata)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database - create tables
    """
    # Import all models to ensure they are registered with Base.metadata
    from app.models import User, ResumeRoastSession, UserActivityLog, SystemMetrics
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """
    Close database connections
    """
    await engine.dispose()