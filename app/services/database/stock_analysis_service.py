"""
Database Service for Stock Analysis
Handles all database operations for stock analysis feature
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, and_, or_
from datetime import datetime, timedelta
import logging
import json
import hashlib

from app.models.stock_analysis import StockAnalysis, StockAnalysisCache

logger = logging.getLogger(__name__)


class StockAnalysisDatabaseService:
    """
    Service for managing stock analysis database operations
    """

    @staticmethod
    async def create_analysis(
        db: AsyncSession,
        user_id: int,
        user_question: str,
        stock_symbol: Optional[str] = None,
        stock_name: Optional[str] = None
    ) -> StockAnalysis:
        """
        Create a new stock analysis record
        """
        try:
            analysis = StockAnalysis(
                user_id=user_id,
                user_question=user_question,
                stock_symbol=stock_symbol,
                stock_name=stock_name,
                analysis_status="pending"
            )
            
            db.add(analysis)
            await db.commit()
            await db.refresh(analysis)
            
            logger.info(f"Created stock analysis record {analysis.id} for user {user_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error creating stock analysis: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_analysis(
        db: AsyncSession,
        analysis_id: int,
        **kwargs
    ) -> Optional[StockAnalysis]:
        """
        Update stock analysis record with results
        """
        try:
            result = await db.execute(
                select(StockAnalysis).filter(StockAnalysis.id == analysis_id)
            )
            analysis = result.scalar_one_or_none()
            
            if not analysis:
                logger.warning(f"Stock analysis {analysis_id} not found")
                return None
            
            # Update fields
            for key, value in kwargs.items():
                if hasattr(analysis, key):
                    setattr(analysis, key, value)
            
            # Update timestamp
            analysis.updated_at = datetime.utcnow()
            
            await db.commit()
            await db.refresh(analysis)
            
            logger.info(f"Updated stock analysis {analysis_id}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error updating stock analysis {analysis_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def get_analysis_by_id(
        db: AsyncSession,
        analysis_id: int,
        user_id: Optional[int] = None
    ) -> Optional[StockAnalysis]:
        """
        Get stock analysis by ID
        Optionally filter by user_id for security
        """
        try:
            query = select(StockAnalysis).filter(StockAnalysis.id == analysis_id)
            
            if user_id is not None:
                query = query.filter(StockAnalysis.user_id == user_id)
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting stock analysis {analysis_id}: {e}")
            raise

    @staticmethod
    async def get_user_analyses(
        db: AsyncSession,
        user_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[StockAnalysis]:
        """
        Get all stock analyses for a user
        """
        try:
            query = (
                select(StockAnalysis)
                .filter(StockAnalysis.user_id == user_id)
                .order_by(desc(StockAnalysis.created_at))
                .limit(limit)
                .offset(offset)
            )
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting user analyses for user {user_id}: {e}")
            raise

    @staticmethod
    async def get_analyses_by_stock(
        db: AsyncSession,
        stock_symbol: str,
        user_id: Optional[int] = None,
        limit: int = 10
    ) -> List[StockAnalysis]:
        """
        Get analyses for a specific stock symbol
        """
        try:
            query = (
                select(StockAnalysis)
                .filter(StockAnalysis.stock_symbol == stock_symbol.upper())
                .filter(StockAnalysis.analysis_status == "completed")
                .order_by(desc(StockAnalysis.created_at))
                .limit(limit)
            )
            
            if user_id is not None:
                query = query.filter(StockAnalysis.user_id == user_id)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting analyses for stock {stock_symbol}: {e}")
            raise

    @staticmethod
    def _generate_cache_key(query: str, data_type: str = "search_data") -> str:
        """
        Generate a hash key for caching
        """
        key_string = f"{query}:{data_type}"
        return hashlib.sha256(key_string.encode()).hexdigest()

    @staticmethod
    async def get_cached_data(
        db: AsyncSession,
        stock_symbol: str,
        query: str,
        data_type: str = "search_data",
        max_age_hours: int = 24
    ) -> Optional[str]:
        """
        Retrieve cached stock data if available and not expired
        """
        try:
            query_hash = StockAnalysisDatabaseService._generate_cache_key(query, data_type)
            
            # Calculate expiry threshold
            expiry_threshold = datetime.utcnow() - timedelta(hours=max_age_hours)
            
            result = await db.execute(
                select(StockAnalysisCache)
                .filter(
                    and_(
                        StockAnalysisCache.stock_symbol == stock_symbol.upper(),
                        StockAnalysisCache.data_type == data_type,
                        StockAnalysisCache.query_hash == query_hash,
                        StockAnalysisCache.is_valid == True,
                        or_(
                            StockAnalysisCache.expires_at.is_(None),
                            StockAnalysisCache.expires_at > datetime.utcnow()
                        ),
                        StockAnalysisCache.created_at > expiry_threshold
                    )
                )
            )
            
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                # Update cache hit counter and last accessed time
                cache_entry.cache_hits += 1
                cache_entry.last_accessed_at = datetime.utcnow()
                await db.commit()
                
                logger.info(f"Cache hit for {stock_symbol} - {data_type}")
                return cache_entry.cached_data
            
            logger.info(f"Cache miss for {stock_symbol} - {data_type}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving cached data: {e}")
            return None

    @staticmethod
    async def cache_data(
        db: AsyncSession,
        stock_symbol: str,
        query: str,
        data: str,
        data_type: str = "search_data",
        expires_hours: Optional[int] = 24
    ) -> StockAnalysisCache:
        """
        Cache stock data for future use
        """
        try:
            query_hash = StockAnalysisDatabaseService._generate_cache_key(query, data_type)
            
            # Calculate expiry time
            expires_at = None
            if expires_hours:
                expires_at = datetime.utcnow() + timedelta(hours=expires_hours)
            
            # Check if cache entry already exists
            result = await db.execute(
                select(StockAnalysisCache)
                .filter(
                    and_(
                        StockAnalysisCache.stock_symbol == stock_symbol.upper(),
                        StockAnalysisCache.data_type == data_type,
                        StockAnalysisCache.query_hash == query_hash
                    )
                )
            )
            
            cache_entry = result.scalar_one_or_none()
            
            if cache_entry:
                # Update existing cache
                cache_entry.cached_data = data
                cache_entry.is_valid = True
                cache_entry.expires_at = expires_at
                cache_entry.last_accessed_at = datetime.utcnow()
            else:
                # Create new cache entry
                cache_entry = StockAnalysisCache(
                    stock_symbol=stock_symbol.upper(),
                    data_type=data_type,
                    query_hash=query_hash,
                    cached_data=data,
                    is_valid=True,
                    expires_at=expires_at
                )
                db.add(cache_entry)
            
            await db.commit()
            await db.refresh(cache_entry)
            
            logger.info(f"Cached data for {stock_symbol} - {data_type}")
            return cache_entry
            
        except Exception as e:
            logger.error(f"Error caching data: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def invalidate_cache(
        db: AsyncSession,
        stock_symbol: Optional[str] = None,
        data_type: Optional[str] = None
    ) -> int:
        """
        Invalidate cached data
        Returns number of invalidated entries
        """
        try:
            query = select(StockAnalysisCache)
            
            if stock_symbol:
                query = query.filter(StockAnalysisCache.stock_symbol == stock_symbol.upper())
            
            if data_type:
                query = query.filter(StockAnalysisCache.data_type == data_type)
            
            result = await db.execute(query)
            cache_entries = result.scalars().all()
            
            count = 0
            for entry in cache_entries:
                entry.is_valid = False
                count += 1
            
            await db.commit()
            
            logger.info(f"Invalidated {count} cache entries")
            return count
            
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            await db.rollback()
            raise


# Create singleton instance
stock_analysis_db_service = StockAnalysisDatabaseService()

__all__ = ["stock_analysis_db_service", "StockAnalysisDatabaseService"]
