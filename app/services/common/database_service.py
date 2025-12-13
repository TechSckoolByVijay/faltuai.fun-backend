"""
Common Database Utilities
Provides reusable database operations across the application
"""
from typing import List, Dict, Any, Optional, TypeVar, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import func, and_, or_
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')

class DatabaseService:
    """Centralized service for common database operations"""
    
    @staticmethod
    async def get_by_id(
        db: AsyncSession, 
        model: Type[T], 
        id: int,
        relationships: Optional[List[str]] = None
    ) -> Optional[T]:
        """
        Get a single record by ID with optional relationship loading
        """
        try:
            query = select(model).filter(model.id == id)
            
            if relationships:
                for rel in relationships:
                    query = query.options(selectinload(getattr(model, rel)))
            
            result = await db.execute(query)
            return result.scalar_one_or_none()
            
        except Exception as e:
            logger.error(f"Error getting {model.__name__} by id {id}: {e}")
            raise
    
    @staticmethod
    async def get_by_conditions(
        db: AsyncSession,
        model: Type[T],
        conditions: Dict[str, Any],
        relationships: Optional[List[str]] = None,
        limit: Optional[int] = None,
        order_by: Optional[str] = None
    ) -> List[T]:
        """
        Get records by multiple conditions
        """
        try:
            query = select(model)
            
            # Apply conditions
            for field, value in conditions.items():
                if hasattr(model, field):
                    query = query.filter(getattr(model, field) == value)
            
            # Load relationships
            if relationships:
                for rel in relationships:
                    if hasattr(model, rel):
                        query = query.options(selectinload(getattr(model, rel)))
            
            # Apply ordering
            if order_by and hasattr(model, order_by):
                query = query.order_by(getattr(model, order_by).desc())
            
            # Apply limit
            if limit:
                query = query.limit(limit)
            
            result = await db.execute(query)
            return result.scalars().all()
            
        except Exception as e:
            logger.error(f"Error getting {model.__name__} records: {e}")
            raise
    
    @staticmethod
    async def create_record(
        db: AsyncSession,
        model: Type[T],
        data: Dict[str, Any],
        commit: bool = True
    ) -> T:
        """
        Create a new record
        """
        try:
            record = model(**data)
            db.add(record)
            
            if commit:
                await db.commit()
                await db.refresh(record)
            else:
                await db.flush()
            
            return record
            
        except Exception as e:
            logger.error(f"Error creating {model.__name__}: {e}")
            if commit:
                await db.rollback()
            raise
    
    @staticmethod
    async def update_record(
        db: AsyncSession,
        record: T,
        data: Dict[str, Any],
        commit: bool = True
    ) -> T:
        """
        Update an existing record
        """
        try:
            for field, value in data.items():
                if hasattr(record, field):
                    setattr(record, field, value)
            
            if commit:
                await db.commit()
                await db.refresh(record)
            
            return record
            
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            if commit:
                await db.rollback()
            raise
    
    @staticmethod
    async def delete_record(
        db: AsyncSession,
        model: Type[T],
        id: int,
        commit: bool = True
    ) -> bool:
        """
        Delete a record by ID
        """
        try:
            record = await DatabaseService.get_by_id(db, model, id)
            if record:
                await db.delete(record)
                if commit:
                    await db.commit()
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting {model.__name__} {id}: {e}")
            if commit:
                await db.rollback()
            raise
    
    @staticmethod
    async def count_records(
        db: AsyncSession,
        model: Type[T],
        conditions: Optional[Dict[str, Any]] = None
    ) -> int:
        """
        Count records matching conditions
        """
        try:
            query = select(func.count(model.id))
            
            if conditions:
                for field, value in conditions.items():
                    if hasattr(model, field):
                        query = query.filter(getattr(model, field) == value)
            
            result = await db.execute(query)
            return result.scalar()
            
        except Exception as e:
            logger.error(f"Error counting {model.__name__} records: {e}")
            raise
    
    @staticmethod
    async def paginate(
        db: AsyncSession,
        model: Type[T],
        page: int = 1,
        per_page: int = 10,
        conditions: Optional[Dict[str, Any]] = None,
        relationships: Optional[List[str]] = None,
        order_by: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Paginate records with metadata
        """
        try:
            offset = (page - 1) * per_page
            
            # Get total count
            total = await DatabaseService.count_records(db, model, conditions)
            
            # Get records for current page
            records = await DatabaseService.get_by_conditions(
                db=db,
                model=model,
                conditions=conditions or {},
                relationships=relationships,
                limit=per_page,
                order_by=order_by
            )
            
            # Skip records for pagination
            query = select(model)
            if conditions:
                for field, value in conditions.items():
                    if hasattr(model, field):
                        query = query.filter(getattr(model, field) == value)
            
            if order_by and hasattr(model, order_by):
                query = query.order_by(getattr(model, order_by).desc())
            
            query = query.offset(offset).limit(per_page)
            
            if relationships:
                for rel in relationships:
                    if hasattr(model, rel):
                        query = query.options(selectinload(getattr(model, rel)))
            
            result = await db.execute(query)
            records = result.scalars().all()
            
            return {
                "records": records,
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page,
                "has_next": page * per_page < total,
                "has_prev": page > 1
            }
            
        except Exception as e:
            logger.error(f"Error paginating {model.__name__}: {e}")
            raise

# Global instance
db_service = DatabaseService()