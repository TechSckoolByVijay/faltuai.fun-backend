"""Database service for product ideas."""

from io import StringIO
import csv
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_idea import ProductIdea
from app.schemas.product_idea import ProductIdeaAdminUpdate, ProductIdeaCreate


class ProductIdeaService:
    @staticmethod
    async def create_idea(db: AsyncSession, payload: ProductIdeaCreate) -> ProductIdea:
        idea = ProductIdea(
            idea_title=payload.idea_title.strip(),
            idea_description=payload.idea_description.strip(),
            target_users=payload.target_users.strip() if payload.target_users else None,
            feature_categories=payload.feature_categories or [],
            usage_frequency=payload.usage_frequency.strip() if payload.usage_frequency else None,
            example_references=payload.example_references.strip() if payload.example_references else None,
            contact_email=str(payload.contact_email).lower() if payload.contact_email else None,
            source=payload.source.strip() if payload.source else "landing_page",
            is_contact_allowed=payload.is_contact_allowed,
            status="new",
        )
        db.add(idea)
        await db.commit()
        await db.refresh(idea)
        return idea

    @staticmethod
    async def list_ideas(
        db: AsyncSession,
        limit: int = 25,
        offset: int = 0,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple[list[ProductIdea], int]:
        filters = []

        if status and status != "all":
            filters.append(ProductIdea.status == status)

        if search:
            normalized = f"%{search.strip()}%"
            filters.append(
                or_(
                    ProductIdea.idea_title.ilike(normalized),
                    ProductIdea.idea_description.ilike(normalized),
                    ProductIdea.target_users.ilike(normalized),
                    ProductIdea.contact_email.ilike(normalized),
                )
            )

        base_query = select(ProductIdea)
        count_query = select(func.count(ProductIdea.id))

        if filters:
            base_query = base_query.where(*filters)
            count_query = count_query.where(*filters)

        base_query = base_query.order_by(ProductIdea.submitted_at.desc()).offset(offset).limit(limit)

        rows_result = await db.execute(base_query)
        total_result = await db.execute(count_query)

        return rows_result.scalars().all(), int(total_result.scalar() or 0)

    @staticmethod
    async def get_idea_by_id(db: AsyncSession, idea_id: int) -> Optional[ProductIdea]:
        result = await db.execute(select(ProductIdea).where(ProductIdea.id == idea_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_idea(db: AsyncSession, idea_id: int, payload: ProductIdeaAdminUpdate) -> Optional[ProductIdea]:
        idea = await ProductIdeaService.get_idea_by_id(db, idea_id)
        if not idea:
            return None

        if payload.status is not None:
            idea.status = payload.status.strip()

        if payload.admin_notes is not None:
            idea.admin_notes = payload.admin_notes.strip() or None

        await db.commit()
        await db.refresh(idea)
        return idea

    @staticmethod
    async def delete_idea(db: AsyncSession, idea_id: int) -> bool:
        idea = await ProductIdeaService.get_idea_by_id(db, idea_id)
        if not idea:
            return False

        await db.delete(idea)
        await db.commit()
        return True

    @staticmethod
    def ideas_to_csv(ideas: list[ProductIdea]) -> str:
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "id",
            "idea_title",
            "idea_description",
            "target_users",
            "feature_categories",
            "usage_frequency",
            "example_references",
            "contact_email",
            "source",
            "is_contact_allowed",
            "status",
            "admin_notes",
            "submitted_at",
            "updated_at",
        ])

        for item in ideas:
            categories = ", ".join(item.feature_categories or [])
            writer.writerow([
                item.id,
                item.idea_title,
                item.idea_description,
                item.target_users or "",
                categories,
                item.usage_frequency or "",
                item.example_references or "",
                item.contact_email or "",
                item.source,
                item.is_contact_allowed,
                item.status,
                item.admin_notes or "",
                item.submitted_at.isoformat() if item.submitted_at else "",
                item.updated_at.isoformat() if item.updated_at else "",
            ])

        return output.getvalue()


product_idea_service = ProductIdeaService()
