"""
Caching service for market research data
Manages cache lifecycle and provides unified interface for all data sources
"""

from typing import Dict, Any, Optional, Callable
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_
import logging
import asyncio

from app.models.market_research_cache import MarketResearchCache

logger = logging.getLogger(__name__)


class MarketResearchCacheService:
    """Service for managing market research data caching"""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_or_fetch(
        self,
        source: str,
        fetch_function: Callable,
        cache_hours: int = 24,
        **query_params
    ) -> Dict[str, Any]:
        """
        Get data from cache or fetch from API if not cached/expired
        
        Args:
            source: API source (serper, github, youtube, hackernews)
            fetch_function: Async function to call if cache miss
            cache_hours: Hours to cache the result
            **query_params: Parameters for the fetch function
            
        Returns:
            Cached or freshly fetched data
        """
        # Generate cache key
        cache_key = MarketResearchCache.generate_cache_key(source, **query_params)
        
        # Try to get from cache
        cached_data = self._get_from_cache(cache_key)
        
        if cached_data:
            logger.info(f"Cache HIT for {source}: {cache_key[:16]}...")
            self._increment_hit_count(cache_key)
            return cached_data
        
        # Cache miss - fetch fresh data
        logger.info(f"Cache MISS for {source}: {cache_key[:16]}... Fetching from API")
        
        try:
            fresh_data = await fetch_function(**query_params)
            
            # Store in cache
            self._store_in_cache(
                cache_key=cache_key,
                source=source,
                query_params=query_params,
                response_data=fresh_data,
                cache_hours=cache_hours
            )
            
            return fresh_data
            
        except Exception as e:
            logger.error(f"Failed to fetch data from {source}: {e}")
            # Return empty dict on error
            return {}
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Retrieve data from cache if not expired"""
        try:
            cache_entry = self.db.query(MarketResearchCache).filter(
                and_(
                    MarketResearchCache.cache_key == cache_key,
                    MarketResearchCache.expires_at > datetime.utcnow()
                )
            ).first()
            
            if cache_entry:
                return cache_entry.response_data
            
        except Exception as e:
            logger.error(f"Cache retrieval error: {e}")
        
        return None
    
    def _store_in_cache(
        self,
        cache_key: str,
        source: str,
        query_params: Dict,
        response_data: Dict[str, Any],
        cache_hours: int
    ):
        """Store data in cache"""
        try:
            # Check if entry already exists
            existing = self.db.query(MarketResearchCache).filter(
                MarketResearchCache.cache_key == cache_key
            ).first()
            
            expires_at = MarketResearchCache.get_expiry_time(cache_hours)
            
            if existing:
                # Update existing entry
                existing.response_data = response_data
                existing.expires_at = expires_at
                existing.last_accessed_at = datetime.utcnow()
                logger.info(f"Updated cache entry: {cache_key[:16]}...")
            else:
                # Create new entry
                cache_entry = MarketResearchCache(
                    cache_key=cache_key,
                    source=source,
                    query_params=query_params,
                    response_data=response_data,
                    expires_at=expires_at,
                    hit_count=0
                )
                self.db.add(cache_entry)
                logger.info(f"Created new cache entry: {cache_key[:16]}...")
            
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Cache storage error: {e}")
            self.db.rollback()
    
    def _increment_hit_count(self, cache_key: str):
        """Increment hit count for cache analytics"""
        try:
            cache_entry = self.db.query(MarketResearchCache).filter(
                MarketResearchCache.cache_key == cache_key
            ).first()
            
            if cache_entry:
                cache_entry.hit_count += 1
                cache_entry.last_accessed_at = datetime.utcnow()
                self.db.commit()
                
        except Exception as e:
            logger.error(f"Hit count increment error: {e}")
            self.db.rollback()
    
    def cleanup_expired_cache(self):
        """Remove expired cache entries"""
        try:
            deleted_count = self.db.query(MarketResearchCache).filter(
                MarketResearchCache.expires_at < datetime.utcnow()
            ).delete()
            
            self.db.commit()
            logger.info(f"Cleaned up {deleted_count} expired cache entries")
            
            return deleted_count
            
        except Exception as e:
            logger.error(f"Cache cleanup error: {e}")
            self.db.rollback()
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_entries = self.db.query(MarketResearchCache).count()
            
            expired_entries = self.db.query(MarketResearchCache).filter(
                MarketResearchCache.expires_at < datetime.utcnow()
            ).count()
            
            active_entries = total_entries - expired_entries
            
            # Get stats by source
            from sqlalchemy import func
            source_stats = self.db.query(
                MarketResearchCache.source,
                func.count(MarketResearchCache.id).label('count'),
                func.sum(MarketResearchCache.hit_count).label('total_hits')
            ).group_by(MarketResearchCache.source).all()
            
            return {
                "total_entries": total_entries,
                "active_entries": active_entries,
                "expired_entries": expired_entries,
                "by_source": [
                    {
                        "source": stat[0],
                        "entries": stat[1],
                        "total_hits": stat[2] or 0
                    }
                    for stat in source_stats
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
