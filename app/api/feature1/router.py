from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import get_current_active_user
from app.schemas.user import User

# Create router for Feature1 endpoints
router = APIRouter(prefix="/feature1", tags=["feature1"])

@router.get("/hello")
async def get_feature1_hello(current_user: User = Depends(get_current_active_user)):
    """
    Feature1 Hello endpoint - demonstrates protected API access
    
    This endpoint:
    - Requires valid JWT authentication
    - Returns a personalized greeting message
    - Serves as a template for other protected endpoints
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        dict: Greeting message with user information
    """
    return {
        "message": f"Hello from Feature1, {current_user.name}! 🚀",
        "user_email": current_user.email,
        "feature": "feature1",
        "status": "active",
        "description": "This is a demonstration of authenticated API access",
        "next_steps": [
            "Add more Feature1 functionality here",
            "Create additional endpoints as needed",
            "Implement business logic for this feature"
        ]
    }

@router.get("/status")
async def get_feature1_status(current_user: User = Depends(get_current_active_user)):
    """
    Feature1 Status endpoint - returns feature information
    
    Args:
        current_user: Authenticated user from JWT token
        
    Returns:
        dict: Feature status and capabilities
    """
    return {
        "feature_name": "Feature1",
        "version": "1.0.0",
        "status": "active",
        "user": current_user.email,
        "capabilities": [
            "JWT Authentication",
            "Protected API Access", 
            "User Information Retrieval",
            "Status Reporting"
        ],
        "endpoints": [
            "GET /feature1/hello - Get personalized greeting",
            "GET /feature1/status - Get feature status"
        ]
    }

# TODO: Add more Feature1 endpoints here
# Examples:
# @router.post("/data")
# @router.get("/data/{item_id}")
# @router.put("/data/{item_id}")
# @router.delete("/data/{item_id}")

# Export router
__all__ = ["router"]