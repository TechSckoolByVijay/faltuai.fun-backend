"""API routes for Product Ideas feature."""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_super_user
from app.schemas.product_idea import (
    ProductIdeaAdminUpdate,
    ProductIdeaCreate,
    ProductIdeaListResponse,
    ProductIdeaResponse,
    ProductIdeaSubmitResponse,
)
from app.schemas.user import User
from app.services.database.product_idea_service import product_idea_service


router = APIRouter(prefix="/product-ideas", tags=["Product Ideas"])

VALID_STATUSES = {"new", "reviewing", "planned", "shipped", "rejected"}


def _normalize_status(value: str) -> str:
    return value.strip().lower().replace(" ", "_")


@router.get("/health")
async def product_ideas_health():
    return {"status": "healthy", "message": "Product Ideas API is working"}


@router.post("/submit", response_model=ProductIdeaSubmitResponse)
async def submit_product_idea(
    payload: ProductIdeaCreate,
    db: AsyncSession = Depends(get_db),
):
    created = await product_idea_service.create_idea(db=db, payload=payload)
    return ProductIdeaSubmitResponse(
        success=True,
        message="Thanks! Your idea has been submitted successfully.",
        data={"idea_id": created.id, "status": created.status},
    )


@router.get("/admin", response_model=ProductIdeaListResponse)
async def list_product_ideas_for_admin(
    status: str = Query(default="all"),
    search: str | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user
    normalized_status = _normalize_status(status)

    if normalized_status != "all" and normalized_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    items, total = await product_idea_service.list_ideas(
        db=db,
        limit=limit,
        offset=offset,
        status=normalized_status,
        search=search,
    )

    response_items = [
        ProductIdeaResponse(
            id=item.id,
            idea_title=item.idea_title,
            idea_description=item.idea_description,
            target_users=item.target_users,
            feature_categories=item.feature_categories or [],
            usage_frequency=item.usage_frequency,
            example_references=item.example_references,
            contact_email=item.contact_email,
            source=item.source,
            is_contact_allowed=item.is_contact_allowed,
            status=item.status,
            admin_notes=item.admin_notes,
            submitted_at=item.submitted_at,
            updated_at=item.updated_at,
        )
        for item in items
    ]

    return ProductIdeaListResponse(items=response_items, total=total, limit=limit, offset=offset)


@router.patch("/admin/{idea_id}", response_model=ProductIdeaResponse)
async def update_product_idea_for_admin(
    idea_id: int,
    payload: ProductIdeaAdminUpdate,
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user

    if payload.status is not None:
        normalized_status = _normalize_status(payload.status)
        if normalized_status not in VALID_STATUSES:
            raise HTTPException(status_code=400, detail="Invalid status value")
        payload.status = normalized_status

    updated = await product_idea_service.update_idea(db=db, idea_id=idea_id, payload=payload)

    if not updated:
        raise HTTPException(status_code=404, detail="Product idea not found")

    return ProductIdeaResponse(
        id=updated.id,
        idea_title=updated.idea_title,
        idea_description=updated.idea_description,
        target_users=updated.target_users,
        feature_categories=updated.feature_categories or [],
        usage_frequency=updated.usage_frequency,
        example_references=updated.example_references,
        contact_email=updated.contact_email,
        source=updated.source,
        is_contact_allowed=updated.is_contact_allowed,
        status=updated.status,
        admin_notes=updated.admin_notes,
        submitted_at=updated.submitted_at,
        updated_at=updated.updated_at,
    )


@router.delete("/admin/{idea_id}")
async def delete_product_idea_for_admin(
    idea_id: int,
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user

    deleted = await product_idea_service.delete_idea(db=db, idea_id=idea_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Product idea not found")

    return {"success": True, "message": "Product idea deleted"}


@router.get("/admin/export/csv")
async def export_product_ideas_csv(
    status: str = Query(default="all"),
    search: str | None = Query(default=None),
    current_user: User = Depends(get_current_super_user),
    db: AsyncSession = Depends(get_db),
):
    _ = current_user

    normalized_status = _normalize_status(status)
    if normalized_status != "all" and normalized_status not in VALID_STATUSES:
        raise HTTPException(status_code=400, detail="Invalid status filter")

    ideas, _ = await product_idea_service.list_ideas(
        db=db,
        limit=5000,
        offset=0,
        status=normalized_status,
        search=search,
    )

    csv_content = product_idea_service.ideas_to_csv(ideas)
    filename = f"product_ideas_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"

    headers = {"Content-Disposition": f"attachment; filename={filename}"}
    return StreamingResponse(iter([csv_content]), media_type="text/csv", headers=headers)
