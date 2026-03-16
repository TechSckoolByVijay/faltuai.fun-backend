"""Product idea submission model for FaltooAI platform."""

from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, JSON
from sqlalchemy.sql import func
from app.core.database import Base


class ProductIdea(Base):
    """Community-submitted product ideas."""

    __tablename__ = "faltu_product_ideas"

    id = Column(Integer, primary_key=True, index=True)
    idea_title = Column(String(220), nullable=False, index=True)
    idea_description = Column(Text, nullable=False)

    target_users = Column(String(220), nullable=True)
    feature_categories = Column(JSON, nullable=True)
    usage_frequency = Column(String(80), nullable=True)
    example_references = Column(Text, nullable=True)
    contact_email = Column(String(255), nullable=True, index=True)

    source = Column(String(80), nullable=False, default="landing_page")
    is_contact_allowed = Column(Boolean, nullable=False, default=False)

    status = Column(String(40), nullable=False, default="new", index=True)
    admin_notes = Column(Text, nullable=True)

    submitted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    def __repr__(self):
        return f"<ProductIdea(id={self.id}, title='{self.idea_title}', status='{self.status}')>"
