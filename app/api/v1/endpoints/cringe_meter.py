import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.cringe import CringeRequest, CringeResponse
from app.schemas.user import User
from app.services.cringe_service import cringe_service
from app.services.database.resume_roast_service import ResumeRoastDatabaseService


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cringe", tags=["cringe-meter"])


@router.post("/analyze", response_model=CringeResponse)
async def analyze_cringe_post(
    request: CringeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    try:
        result = await cringe_service.analyze_post(request.content)

        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="linkedin_cringe_analysis",
            endpoint="/api/v1/cringe/analyze",
            request_data={
                "content_length": len(request.content),
                "payload": {
                    "cringe_score": result.cringe_score,
                    "buzzwords_detected": result.buzzwords_detected,
                    "roast_verdict": result.roast_verdict,
                },
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
        logger.error(f"Cringe analysis failed: {exc}")

        try:
            await ResumeRoastDatabaseService.log_user_activity(
                db=db,
                user_id=current_user.id,
                activity_type="linkedin_cringe_analysis",
                endpoint="/api/v1/cringe/analyze",
                request_data={"content_length": len(request.content)},
                response_status="error",
                error_message=str(exc),
                ip_address=getattr(http_request.client, "host", None) if http_request else None,
                user_agent=http_request.headers.get("user-agent") if http_request else None,
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to analyze post cringe level. Please try again.",
        )
