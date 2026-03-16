"""Pydantic schemas for product idea submissions."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ProductIdeaCreate(BaseModel):
    idea_title: str = Field(..., min_length=3, max_length=220)
    idea_description: str = Field(..., min_length=10, max_length=5000)

    target_users: Optional[str] = Field(None, max_length=220)
    feature_categories: List[str] = Field(default_factory=list)
    usage_frequency: Optional[str] = Field(None, max_length=80)
    example_references: Optional[str] = Field(None, max_length=2000)
    contact_email: EmailStr

    source: str = Field(default="landing_page", max_length=80)
    is_contact_allowed: bool = False


class ProductIdeaResponse(BaseModel):
    id: int
    idea_title: str
    idea_description: str
    target_users: Optional[str] = None
    feature_categories: List[str] = Field(default_factory=list)
    usage_frequency: Optional[str] = None
    example_references: Optional[str] = None
    contact_email: Optional[str] = None
    source: str
    is_contact_allowed: bool
    status: str
    admin_notes: Optional[str] = None
    submitted_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductIdeaSubmitResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None


class ProductIdeaAdminUpdate(BaseModel):
    status: Optional[str] = Field(default=None, max_length=40)
    admin_notes: Optional[str] = Field(default=None, max_length=2000)


class ProductIdeaListResponse(BaseModel):
    items: List[ProductIdeaResponse]
    total: int
    limit: int
    offset: int
