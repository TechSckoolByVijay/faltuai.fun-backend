"""
Database model for caching market research data
Stores API responses to reduce costs and improve performance
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Index
from sqlalchemy.sql import func
from datetime import datetime, timedelta
from app.core.database import Base


class MarketResearchCache(Base):
    """
    Cache for market research API responses
    
    Stores results from Serper, GitHub, YouTube, HackerNews APIs
    to avoid redundant calls for the same queries within 24-48 hours
    """
    __tablename__ = "market_research_cache"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key (combination of API source + query parameters)
    cache_key = Column(String(512), unique=True, index=True, nullable=False)
    
    # API source identifier
    source = Column(String(50), index=True, nullable=False)  # serper, github, youtube, hackernews
    
    # Query parameters as JSON
    query_params = Column(JSON, nullable=False)
    
    # Cached response data
    response_data = Column(JSON, nullable=False)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), index=True, nullable=False)
    hit_count = Column(Integer, default=0)  # Number of times this cache was used
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add composite index for efficient lookups
    __table_args__ = (
        Index('idx_source_cache_key', 'source', 'cache_key'),
        Index('idx_expires_at', 'expires_at'),
    )
    
    @staticmethod
    def generate_cache_key(source: str, **kwargs) -> str:
        """
        Generate a consistent cache key from query parameters
        
        Args:
            source: API source (serper, github, youtube, hackernews)
            **kwargs: Query parameters
            
        Returns:
            SHA256 hash of the normalized parameters
        """
        import hashlib
        import json
        
        # Sort parameters for consistent hashing
        normalized = json.dumps(kwargs, sort_keys=True)
        key_string = f"{source}:{normalized}"
        
        return hashlib.sha256(key_string.encode()).hexdigest()
    
    @staticmethod
    def get_expiry_time(hours: int = 24) -> datetime:
        """Get expiry datetime (default 24 hours from now)"""
        return datetime.utcnow() + timedelta(hours=hours)
