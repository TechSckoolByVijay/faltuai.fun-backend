"""
Database service for Email Smoothener feature.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.email_smoothener import EmailSmoothenerSession


class EmailSmoothenerDatabaseService:
    @staticmethod
    async def save_session(
        db: AsyncSession,
        user_id: int,
        raw_text: str,
        result_json: dict,
        processing_time_ms: int | None = None,
    ) -> EmailSmoothenerSession:
        session = EmailSmoothenerSession(
            user_id=user_id,
            raw_text=raw_text,
            result_json=result_json,
            processing_time_ms=processing_time_ms,
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session


email_smoothener_db_service = EmailSmoothenerDatabaseService()
