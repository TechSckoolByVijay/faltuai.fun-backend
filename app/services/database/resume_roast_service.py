"""
Resume roast service for database operations related to resume roasting
"""
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.sql import func

from app.models.resume_roast import ResumeRoastSession, UserActivityLog, SystemMetrics
from app.schemas.resume import ResumeRoastResponse


class ResumeRoastDatabaseService:
    """Service class for resume roast database operations"""

    @staticmethod
    async def save_roast_session(
        db: AsyncSession,
        user_id: int,
        resume_text: str,
        roast_style: str,
        roast_result: str,
        suggestions: List[str] = None,
        confidence_score: float = None,
        processing_time_ms: int = None,
        original_filename: str = None,
        file_type: str = None
    ) -> ResumeRoastSession:
        """
        Save a resume roasting session to the database
        
        Args:
            db: Database session
            user_id: User ID
            resume_text: Original resume text
            roast_style: Style used for roasting
            roast_result: Generated roast result
            suggestions: List of suggestions (optional)
            confidence_score: Confidence score (optional)
            processing_time_ms: Processing time in milliseconds
            original_filename: Original filename if uploaded
            file_type: File type if uploaded
            
        Returns:
            ResumeRoastSession: Created session instance
        """
        db_session = ResumeRoastSession(
            user_id=user_id,
            resume_text=resume_text,
            roast_style=roast_style,
            roast_result=roast_result,
            suggestions=suggestions,
            confidence_score=confidence_score,
            processing_time_ms=processing_time_ms,
            original_filename=original_filename,
            file_type=file_type
        )
        
        db.add(db_session)
        await db.commit()
        await db.refresh(db_session)
        return db_session

    @staticmethod
    async def get_user_roast_history(
        db: AsyncSession,
        user_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> List[ResumeRoastSession]:
        """
        Get user's roast session history
        
        Args:
            db: Database session
            user_id: User ID
            limit: Number of sessions to retrieve
            offset: Offset for pagination
            
        Returns:
            List[ResumeRoastSession]: List of roast sessions
        """
        result = await db.execute(
            select(ResumeRoastSession)
            .where(ResumeRoastSession.user_id == user_id)
            .order_by(desc(ResumeRoastSession.created_at))
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def get_roast_session_by_id(
        db: AsyncSession,
        session_id: int,
        user_id: int
    ) -> Optional[ResumeRoastSession]:
        """
        Get a specific roast session by ID (with user verification)
        
        Args:
            db: Database session
            session_id: Session ID
            user_id: User ID for verification
            
        Returns:
            Optional[ResumeRoastSession]: Roast session or None
        """
        result = await db.execute(
            select(ResumeRoastSession)
            .where(
                ResumeRoastSession.id == session_id,
                ResumeRoastSession.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def log_user_activity(
        db: AsyncSession,
        user_id: int,
        activity_type: str,
        endpoint: str = None,
        request_data: dict = None,
        response_status: str = "success",
        error_message: str = None,
        ip_address: str = None,
        user_agent: str = None
    ) -> UserActivityLog:
        """
        Log user activity
        
        Args:
            db: Database session
            user_id: User ID
            activity_type: Type of activity
            endpoint: API endpoint
            request_data: Request parameters
            response_status: Response status
            error_message: Error message if any
            ip_address: User's IP address
            user_agent: User agent string
            
        Returns:
            UserActivityLog: Created activity log
        """
        activity_log = UserActivityLog(
            user_id=user_id,
            activity_type=activity_type,
            endpoint=endpoint,
            request_data=request_data,
            response_status=response_status,
            error_message=error_message,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(activity_log)
        await db.commit()
        await db.refresh(activity_log)
        return activity_log

    @staticmethod
    async def record_system_metric(
        db: AsyncSession,
        metric_name: str,
        metric_value: float,
        metric_unit: str = None,
        tags: dict = None
    ) -> SystemMetrics:
        """
        Record a system metric
        
        Args:
            db: Database session
            metric_name: Name of the metric
            metric_value: Value of the metric
            metric_unit: Unit of measurement
            tags: Additional metadata
            
        Returns:
            SystemMetrics: Created metric record
        """
        metric = SystemMetrics(
            metric_name=metric_name,
            metric_value=metric_value,
            metric_unit=metric_unit,
            tags=tags
        )
        
        db.add(metric)
        await db.commit()
        await db.refresh(metric)
        return metric

    @staticmethod
    async def get_user_roast_count(db: AsyncSession, user_id: int) -> int:
        """
        Get total number of roasts by user
        
        Args:
            db: Database session
            user_id: User ID
            
        Returns:
            int: Number of roasts
        """
        result = await db.execute(
            select(func.count(ResumeRoastSession.id))
            .where(ResumeRoastSession.user_id == user_id)
        )
        return result.scalar() or 0

    @staticmethod
    async def get_daily_roast_stats(
        db: AsyncSession,
        days: int = 7
    ) -> List[dict]:
        """
        Get daily roast statistics for the last N days
        
        Args:
            db: Database session
            days: Number of days to look back
            
        Returns:
            List[dict]: Daily statistics
        """
        result = await db.execute(
            select(
                func.date(ResumeRoastSession.created_at).label('date'),
                func.count(ResumeRoastSession.id).label('count')
            )
            .where(ResumeRoastSession.created_at >= func.now() - func.interval(f'{days} days'))
            .group_by(func.date(ResumeRoastSession.created_at))
            .order_by(desc('date'))
        )
        
        return [{"date": row.date, "count": row.count} for row in result.fetchall()]