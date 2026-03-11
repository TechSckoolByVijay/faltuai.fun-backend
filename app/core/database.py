"""
Database configuration module for SQLAlchemy with PostgreSQL
"""
import os
import logging
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import MetaData
from typing import AsyncGenerator
from urllib.parse import urlparse


logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://faltuai_user:faltuai_password@localhost:5432/faltuai_db")

def _normalize_async_database_url(database_url: str, explicit_async_url: str | None) -> str:
    """Normalize DB URL for SQLAlchemy asyncpg, including Azure SSL query params."""
    # Treat empty string the same as None (happens when GitHub secret is unset)
    async_url = (explicit_async_url or "").strip() or database_url

    if not async_url:
        raise ValueError(
            "No database URL configured. Set DATABASE_URL or ASYNC_DATABASE_URL environment variable."
        )

    if async_url.startswith("postgresql://"):
        async_url = async_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if "sslmode=require" in async_url:
        async_url = async_url.replace("sslmode=require", "ssl=require")

    return async_url


# Use explicit ASYNC_DATABASE_URL if provided (non-empty), otherwise convert from DATABASE_URL
ASYNC_DATABASE_URL = _normalize_async_database_url(
    database_url=DATABASE_URL,
    explicit_async_url=os.getenv("ASYNC_DATABASE_URL")
)

try:
    parsed_db_url = urlparse(ASYNC_DATABASE_URL)
    logger.info(
        "Database config loaded (host=%s, db=%s, async_url=%s)",
        parsed_db_url.hostname,
        parsed_db_url.path.lstrip("/") if parsed_db_url.path else "",
        bool(os.getenv("ASYNC_DATABASE_URL")),
    )
except Exception:
    logger.warning("Database config loaded, but URL parsing failed")

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