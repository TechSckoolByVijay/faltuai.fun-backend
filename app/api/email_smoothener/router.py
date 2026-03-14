import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.email_smoothener import EmailSmoothenerRequest, EmailSmoothenerResponse
from app.schemas.user import User
from app.services.database.email_smoothener_service import email_smoothener_db_service
from app.services.database.resume_roast_service import ResumeRoastDatabaseService
from app.services.email_smoothener_service import email_smoothener_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/email-smoothener", tags=["Email Smoothener"])


@router.post("/smoothen", response_model=EmailSmoothenerResponse)
async def smoothen_email(
    request: EmailSmoothenerRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    start_time = time.time()

    try:
        result = await email_smoothener_service.smoothen_email(request.raw_text)
        processing_time_ms = int((time.time() - start_time) * 1000)

        await email_smoothener_db_service.save_session(
            db=db,
            user_id=current_user.id,
            raw_text=request.raw_text,
            result_json=result.model_dump(),
            processing_time_ms=processing_time_ms,
        )

        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="esm_smoothen",
            endpoint="/api/v1/email-smoothener/smoothen",
            request_data={
                "raw_text": request.raw_text,
                "raw_text_length": len(request.raw_text),
                "variants_count": len(result.variants),
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
        logger.error(f"Email smoothener failed: {exc}")

        try:
            await ResumeRoastDatabaseService.log_user_activity(
                db=db,
                user_id=current_user.id,
                activity_type="esm_smoothen",
                endpoint="/api/v1/email-smoothener/smoothen",
                request_data={"raw_text_length": len(request.raw_text)},
                response_status="error",
                error_message=str(exc),
                ip_address=getattr(http_request.client, "host", None) if http_request else None,
                user_agent=http_request.headers.get("user-agent") if http_request else None,
            )
        except Exception:
            pass

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to smoothen email draft. Please try again.",
        )
