"""
Newsletter subscription model for FaltooAI platform.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text
from sqlalchemy.sql import func
from app.core.database import Base


class NewsletterSubscription(Base):
    """Newsletter subscription model for storing subscriber information."""
    
    __tablename__ = "newsletter_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    subscribed_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True, nullable=False)
    unsubscribe_token = Column(String(255), unique=True, nullable=True)
    source = Column(String(100), default="website", nullable=True)  # Track where subscription came from
    user_agent = Column(Text, nullable=True)  # Optional: track user agent for analytics
    ip_address = Column(String(45), nullable=True)  # Optional: track IP for analytics
    confirmed_at = Column(DateTime(timezone=True), nullable=True)  # For double opt-in if needed
    unsubscribed_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<NewsletterSubscription(email='{self.email}', active={self.is_active})>"