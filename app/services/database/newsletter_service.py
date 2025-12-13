"""
Newsletter subscription database service.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func
from sqlalchemy import select
from app.models.newsletter_subscription import NewsletterSubscription
from app.schemas.newsletter import NewsletterSubscriptionCreate
from typing import Optional, List
import secrets
import string


class NewsletterSubscriptionService:
    """Service for managing newsletter subscriptions."""
    
    @staticmethod
    async def create_subscription(
        db: AsyncSession,
        subscription_data: NewsletterSubscriptionCreate,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None
    ) -> Optional[NewsletterSubscription]:
        """
        Create a new newsletter subscription.
        
        Args:
            db: Database session
            subscription_data: Subscription data
            user_agent: User agent string
            ip_address: IP address of subscriber
            
        Returns:
            Created subscription or None if email already exists
        """
        try:
            # Generate unsubscribe token
            unsubscribe_token = ''.join(
                secrets.choice(string.ascii_letters + string.digits) 
                for _ in range(32)
            )
            
            db_subscription = NewsletterSubscription(
                email=subscription_data.email.lower(),  # Normalize email
                source=subscription_data.source,
                user_agent=user_agent,
                ip_address=ip_address,
                unsubscribe_token=unsubscribe_token,
                is_active=True
            )
            
            db.add(db_subscription)
            await db.commit()
            await db.refresh(db_subscription)
            return db_subscription
            
        except IntegrityError:
            # Email already exists
            await db.rollback()
            return None
    
    @staticmethod
    async def get_subscription_by_email(
        db: AsyncSession, 
        email: str
    ) -> Optional[NewsletterSubscription]:
        """Get subscription by email address."""
        stmt = select(NewsletterSubscription).where(
            NewsletterSubscription.email == email.lower()
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()
    
    @staticmethod
    async def unsubscribe_by_email(db: AsyncSession, email: str) -> bool:
        """
        Unsubscribe user by email address.
        
        Args:
            db: Database session
            email: Email to unsubscribe
            
        Returns:
            True if successfully unsubscribed, False otherwise
        """
        subscription = await NewsletterSubscriptionService.get_subscription_by_email(db, email)
        if subscription and subscription.is_active:
            subscription.is_active = False
            subscription.unsubscribed_at = func.now()
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def resubscribe_by_email(db: AsyncSession, email: str) -> bool:
        """
        Reactivate subscription for an email address.
        
        Args:
            db: Database session
            email: Email to resubscribe
            
        Returns:
            True if successfully resubscribed, False otherwise
        """
        subscription = await NewsletterSubscriptionService.get_subscription_by_email(db, email)
        if subscription and not subscription.is_active:
            subscription.is_active = True
            subscription.unsubscribed_at = None
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def get_active_subscriptions(
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 1000
    ) -> List[NewsletterSubscription]:
        """Get all active newsletter subscriptions."""
        stmt = select(NewsletterSubscription).where(
            NewsletterSubscription.is_active == True
        ).offset(skip).limit(limit)
        result = await db.execute(stmt)
        return result.scalars().all()
    
    @staticmethod
    async def get_subscription_stats(db: AsyncSession) -> dict:
        """Get newsletter subscription statistics."""
        total_stmt = select(func.count(NewsletterSubscription.id))
        total_result = await db.execute(total_stmt)
        total_subscriptions = total_result.scalar()
        
        active_stmt = select(func.count(NewsletterSubscription.id)).where(
            NewsletterSubscription.is_active == True
        )
        active_result = await db.execute(active_stmt)
        active_subscriptions = active_result.scalar()
        
        unsubscribed = total_subscriptions - active_subscriptions
        
        return {
            "total_subscriptions": total_subscriptions,
            "active_subscriptions": active_subscriptions,
            "unsubscribed": unsubscribed,
            "conversion_rate": round(
                (active_subscriptions / total_subscriptions * 100) if total_subscriptions > 0 else 0,
                2
            )
        }