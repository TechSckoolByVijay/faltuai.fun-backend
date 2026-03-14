from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_super_user
from app.schemas.admin_analytics import (
    AnalyticsOverviewResponse,
    FeatureQuestionsResponse,
    FeatureUsersResponse,
)
from app.schemas.user import User
from app.services.admin_analytics_service import admin_analytics_service


router = APIRouter(prefix="/admin", tags=["Admin Analytics"])


@router.get("/analytics/overview", response_model=AnalyticsOverviewResponse)
async def get_analytics_overview(
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    return await admin_analytics_service.get_overview(db)


@router.get("/analytics/features/{feature_key}/users", response_model=FeatureUsersResponse)
async def get_feature_users(
    feature_key: str,
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    try:
        return await admin_analytics_service.get_feature_users(db, feature_key=feature_key, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/analytics/features/{feature_key}/questions", response_model=FeatureQuestionsResponse)
async def get_feature_questions(
    feature_key: str,
    limit: int = Query(default=15, ge=1, le=100),
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    try:
        return await admin_analytics_service.get_feature_common_questions(db, feature_key=feature_key, limit=limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
