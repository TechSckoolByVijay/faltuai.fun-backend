import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.name_craft import NameCraftRequest, NameCraftResponse
from app.schemas.user import User
from app.services.database.resume_roast_service import ResumeRoastDatabaseService
from app.services.name_craft_service import name_craft_service


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/name-craft", tags=["name-craft"])


@router.post("/generate", response_model=NameCraftResponse)
async def generate_name_conventions(
    request: NameCraftRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None,
):
    try:
        result = await name_craft_service.generate_names(request)

        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="name_craft_generate",
            endpoint="/api/v1/name-craft/generate",
            request_data={
                "project_name_length": len(request.project_name),
                "project_type": request.project_type,
                "naming_preference": request.naming_preference,
                "advanced_options_enabled": request.advanced_options_enabled,
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
        logger.error(f"NameCraft generation failed: {exc}")

        try:
            await ResumeRoastDatabaseService.log_user_activity(
                db=db,
                user_id=current_user.id,
                activity_type="name_craft_generate",
                endpoint="/api/v1/name-craft/generate",
                request_data={
                    "project_name_length": len(request.project_name),
                    "project_type": request.project_type,
                    "naming_preference": request.naming_preference,
                    "advanced_options_enabled": request.advanced_options_enabled,
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
            detail="Failed to generate naming suggestions. Please try again.",
        )
