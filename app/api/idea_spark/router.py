import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.idea_spark import IdeaSparkRequest, IdeaSparkResponse
from app.schemas.user import User
from app.services.database.resume_roast_service import ResumeRoastDatabaseService
from app.services.idea_spark_service import idea_spark_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/idea-spark", tags=["idea-spark"])


@router.post("/generate", response_model=IdeaSparkResponse)
async def generate_ideas(
    request: IdeaSparkRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    try:
        result = await idea_spark_service.spark_ideas(request)

        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="idea_spark_generate",
            endpoint="/api/v1/idea-spark/generate",
            request_data={
                "phrase_length": len(request.phrase),
                "ideas_count": len(result.ideas),
                "time_available": request.time_available,
                "create_type": request.create_type,
                "skill_area": request.skill_area,
                "difficulty_level": request.difficulty_level,
            },
            response_status="success",
            ip_address=getattr(http_request.client, "host", None) if http_request else None,
            user_agent=http_request.headers.get("user-agent") if http_request else None,
        )

        return result

    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Idea Spark generation failed: {exc}")

        try:
            await ResumeRoastDatabaseService.log_user_activity(
                db=db,
                user_id=current_user.id,
                activity_type="idea_spark_generate",
                endpoint="/api/v1/idea-spark/generate",
                request_data={
                    "phrase_length": len(request.phrase),
                    "time_available": request.time_available,
                    "create_type": request.create_type,
                    "skill_area": request.skill_area,
                    "difficulty_level": request.difficulty_level,
                },
                response_status="error",
                error_message=str(exc),
                ip_address=getattr(http_request.client, "host", None) if http_request else None,
                user_agent=http_request.headers.get("user-agent") if http_request else None,
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to spark ideas. Please try again.",
        )
