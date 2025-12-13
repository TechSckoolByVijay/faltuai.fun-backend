"""
Newsletter subscription API routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.newsletter import (
    NewsletterSubscriptionCreate,
    NewsletterSubscriptionResponse,
    NewsletterUnsubscribeRequest,
    NewsletterStatusResponse
)
from app.services.database.newsletter_service import NewsletterSubscriptionService
from typing import List

router = APIRouter(prefix="/newsletter", tags=["Newsletter"])


@router.post("/subscribe", response_model=NewsletterStatusResponse)
async def subscribe_to_newsletter(
    subscription_data: NewsletterSubscriptionCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Subscribe to FaltooAI monthly newsletter.
    
    Subscribe to receive curated AI updates and insights delivered monthly.
    We promise to keep you ahead in the AI race without spam!
    """
    # Extract client information
    user_agent = request.headers.get("user-agent")
    client_ip = request.client.host if request.client else None
    
    # Check if email already exists
    existing_subscription = NewsletterSubscriptionService.get_subscription_by_email(
        db, subscription_data.email
    )
    
    if existing_subscription:
        if existing_subscription.is_active:
            return NewsletterStatusResponse(
                success=False,
                message="You're already subscribed to our newsletter! Check your inbox for our latest updates.",
                data={"status": "already_subscribed"}
            )
        else:
            # Reactivate subscription
            reactivated = NewsletterSubscriptionService.resubscribe_by_email(
                db, subscription_data.email
            )
            if reactivated:
                return NewsletterStatusResponse(
                    success=True,
                    message="Welcome back! Your newsletter subscription has been reactivated.",
                    data={"status": "reactivated"}
                )
    
    # Create new subscription
    new_subscription = NewsletterSubscriptionService.create_subscription(
        db=db,
        subscription_data=subscription_data,
        user_agent=user_agent,
        ip_address=client_ip
    )
    
    if new_subscription:
        return NewsletterStatusResponse(
            success=True,
            message="🎉 Successfully subscribed! Get ready for curated AI insights delivered monthly.",
            data={
                "status": "subscribed",
                "subscription_id": new_subscription.id,
                "email": new_subscription.email
            }
        )
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to process subscription. Please try again."
        )


@router.post("/unsubscribe", response_model=NewsletterStatusResponse)
async def unsubscribe_from_newsletter(
    unsubscribe_data: NewsletterUnsubscribeRequest,
    db: Session = Depends(get_db)
):
    """
    Unsubscribe from newsletter.
    
    Remove email address from our newsletter mailing list.
    """
    success = NewsletterSubscriptionService.unsubscribe_by_email(
        db, unsubscribe_data.email
    )
    
    if success:
        return NewsletterStatusResponse(
            success=True,
            message="You've been successfully unsubscribed. We're sorry to see you go!",
            data={"status": "unsubscribed"}
        )
    else:
        return NewsletterStatusResponse(
            success=False,
            message="Email not found in our subscription list.",
            data={"status": "not_found"}
        )


@router.get("/check/{email}", response_model=NewsletterStatusResponse)
async def check_subscription_status(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check newsletter subscription status for an email.
    """
    subscription = NewsletterSubscriptionService.get_subscription_by_email(db, email)
    
    if subscription:
        return NewsletterStatusResponse(
            success=True,
            message="Subscription found",
            data={
                "is_subscribed": subscription.is_active,
                "subscribed_at": subscription.subscribed_at.isoformat() if subscription.subscribed_at else None,
                "source": subscription.source
            }
        )
    else:
        return NewsletterStatusResponse(
            success=False,
            message="Email not found in subscription list",
            data={"is_subscribed": False}
        )


@router.get("/stats", response_model=NewsletterStatusResponse)
async def get_newsletter_stats(db: Session = Depends(get_db)):
    """
    Get newsletter subscription statistics.
    
    Note: This endpoint should be protected in production.
    """
    stats = NewsletterSubscriptionService.get_subscription_stats(db)
    
    return NewsletterStatusResponse(
        success=True,
        message="Newsletter statistics retrieved successfully",
        data=stats
    )