"""
Newsletter subscription Pydantic schemas.
"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional


class NewsletterSubscriptionBase(BaseModel):
    """Base newsletter subscription schema."""
    email: EmailStr = Field(..., description="Subscriber's email address")


class NewsletterSubscriptionCreate(NewsletterSubscriptionBase):
    """Schema for creating newsletter subscription."""
    source: Optional[str] = Field("website", description="Source of subscription")


class NewsletterSubscriptionResponse(BaseModel):
    """Schema for newsletter subscription response."""
    id: int
    email: str
    subscribed_at: datetime
    is_active: bool
    source: Optional[str]
    
    class Config:
        from_attributes = True


class NewsletterUnsubscribeRequest(BaseModel):
    """Schema for unsubscribe request."""
    email: EmailStr = Field(..., description="Email to unsubscribe")


class NewsletterStatusResponse(BaseModel):
    """Schema for subscription status response."""
    success: bool
    message: str
    data: Optional[dict] = None