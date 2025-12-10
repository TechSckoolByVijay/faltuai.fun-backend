from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException, status, Request
from typing import Optional
import logging
import time

from app.core.security import get_current_active_user
from app.core.database import get_db
from app.schemas.user import User
from app.schemas.resume import ResumeRoastRequest, ResumeRoastResponse, FileUploadResponse
from app.services.resume_roasting_service import resume_roasting_service
from app.services.document_processor import DocumentProcessor
from app.services.database.resume_roast_service import ResumeRoastDatabaseService
from sqlalchemy.ext.asyncio import AsyncSession

# Create router for Resume Roast endpoints
router = APIRouter(prefix="/resume-roast", tags=["resume-roast"])

logger = logging.getLogger(__name__)

@router.get("/styles")
async def get_roasting_styles(current_user: User = Depends(get_current_active_user)):
    """
    Get available roasting styles
    
    Returns:
        dict: Available roasting styles with descriptions
    """
    return {
        "styles": resume_roasting_service.get_available_styles(),
        "message": "Available roasting styles for your resume review"
    }

@router.post("/roast-text", response_model=ResumeRoastResponse)
async def roast_resume_text(
    request: ResumeRoastRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None
):
    """
    Roast a resume from text input
    
    Args:
        request: Resume roasting request with text and style
        current_user: Authenticated user
        db: Database session
        http_request: HTTP request for logging
        
    Returns:
        ResumeRoastResponse: Roasting results with feedback and suggestions
    """
    start_time = time.time()
    
    try:
        # Validate input
        if not request.resume_text.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text cannot be empty"
            )
        
        if len(request.resume_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resume text is too short. Please provide a more complete resume."
            )
        
        # Roast the resume
        result = await resume_roasting_service.roast_resume(
            resume_text=request.resume_text,
            style=request.roast_style
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save session to database
        await ResumeRoastDatabaseService.save_roast_session(
            db=db,
            user_id=current_user.id,
            resume_text=request.resume_text,
            roast_style=request.roast_style,
            roast_result=result["roast"],
            suggestions=result.get("suggestions"),
            confidence_score=result.get("confidence_score"),
            processing_time_ms=processing_time_ms
        )
        
        # Log user activity
        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="resume_roast_text",
            endpoint="/api/v1/resume-roast/roast-text",
            request_data={"style": request.roast_style, "text_length": len(request.resume_text)},
            response_status="success",
            ip_address=getattr(http_request.client, 'host', None) if http_request else None,
            user_agent=http_request.headers.get('user-agent') if http_request else None
        )
        
        logger.info(f"Resume roasted for user {current_user.email} with style {request.roast_style}")
        
        return ResumeRoastResponse(**result)
        
    except HTTPException:
        # Log failed attempt
        if 'db' in locals():
            try:
                await ResumeRoastDatabaseService.log_user_activity(
                    db=db,
                    user_id=current_user.id,
                    activity_type="resume_roast_text",
                    endpoint="/api/v1/resume-roast/roast-text",
                    response_status="error",
                    error_message="Validation error"
                )
            except:
                pass  # Don't fail the request if logging fails
        raise
    except Exception as e:
        # Log error
        if 'db' in locals():
            try:
                await ResumeRoastDatabaseService.log_user_activity(
                    db=db,
                    user_id=current_user.id,
                    activity_type="resume_roast_text",
                    endpoint="/api/v1/resume-roast/roast-text",
                    response_status="error",
                    error_message=str(e)
                )
            except:
                pass  # Don't fail the request if logging fails
        
        logger.error(f"Error roasting resume text: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to roast resume. Please try again."
        )

@router.post("/upload-and-roast", response_model=ResumeRoastResponse)
async def upload_and_roast_resume(
    file: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    roast_style: str = Form("funny", description="Roasting style"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    http_request: Request = None
):
    """
    Upload a resume file and roast it
    
    Args:
        file: Uploaded resume file (PDF or TXT)
        roast_style: Style of roasting (funny, professional, brutal, constructive)
        current_user: Authenticated user
        db: Database session
        http_request: HTTP request for logging
        
    Returns:
        ResumeRoastResponse: Roasting results with feedback and suggestions
    """
    start_time = time.time()
    
    try:
        # Process the uploaded file
        document_processor = DocumentProcessor()
        extracted_text = await document_processor.process_file(file)
        
        # Validate extracted text
        if len(extracted_text) < 50:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Extracted text is too short. Please upload a more complete resume."
            )
        
        # Roast the resume
        result = await resume_roasting_service.roast_resume(
            resume_text=extracted_text,
            style=roast_style
        )
        
        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)
        
        # Save session to database
        await ResumeRoastDatabaseService.save_roast_session(
            db=db,
            user_id=current_user.id,
            original_filename=file.filename,
            file_type=file.content_type,
            resume_text=extracted_text,
            roast_style=roast_style,
            roast_result=result["roast"],
            suggestions=result.get("suggestions"),
            confidence_score=result.get("confidence_score"),
            processing_time_ms=processing_time_ms
        )
        
        # Log user activity
        await ResumeRoastDatabaseService.log_user_activity(
            db=db,
            user_id=current_user.id,
            activity_type="resume_roast_upload",
            endpoint="/api/v1/resume-roast/upload-and-roast",
            request_data={"style": roast_style, "filename": file.filename, "text_length": len(extracted_text)},
            response_status="success",
            ip_address=getattr(http_request.client, 'host', None) if http_request else None,
            user_agent=http_request.headers.get('user-agent') if http_request else None
        )
        
        logger.info(f"Resume file roasted for user {current_user.email} - file: {file.filename}, style: {roast_style}")
        
        return ResumeRoastResponse(**result)
        
    except HTTPException:
        # Log failed attempt
        if 'db' in locals():
            try:
                await ResumeRoastDatabaseService.log_user_activity(
                    db=db,
                    user_id=current_user.id,
                    activity_type="resume_roast_upload",
                    endpoint="/api/v1/resume-roast/upload-and-roast",
                    response_status="error",
                    error_message="Validation error"
                )
            except:
                pass  # Don't fail the request if logging fails
        raise
    except Exception as e:
        # Log error
        if 'db' in locals():
            try:
                await ResumeRoastDatabaseService.log_user_activity(
                    db=db,
                    user_id=current_user.id,
                    activity_type="resume_roast_upload",
                    endpoint="/api/v1/resume-roast/upload-and-roast",
                    response_status="error",
                    error_message=str(e)
                )
            except:
                pass  # Don't fail the request if logging fails
        
        logger.error(f"Error processing file upload and roasting: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process file and roast resume. Please try again."
        )

@router.post("/extract-text", response_model=FileUploadResponse)
async def extract_text_from_file(
    file: UploadFile = File(..., description="Resume file (PDF or TXT)"),
    current_user: User = Depends(get_current_active_user)
):
    """
    Extract text from uploaded resume file without roasting
    Useful for previewing extracted content before roasting
    
    Args:
        file: Uploaded resume file
        current_user: Authenticated user
        
    Returns:
        FileUploadResponse: Extracted text and file information
    """
    try:
        # Process the uploaded file
        document_processor = DocumentProcessor()
        extracted_text = await document_processor.process_file(file)
        
        return FileUploadResponse(
            filename=file.filename or "unknown",
            file_type=file.content_type or "unknown",
            extracted_text=extracted_text,
            message=f"Successfully extracted {len(extracted_text)} characters from {file.filename}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting text from file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract text from file. Please try again."
        )

@router.get("/test")
async def test_roast():
    """
    Simple test endpoint to verify LangChain and LangSmith integration (no auth required)
    
    Returns:
        dict: Test roasting result
    """
    test_resume = "John Doe - Software Engineer with 2 years experience"
    
    # Verify LangSmith setup first
    langsmith_status = resume_roasting_service.verify_langsmith_setup()
    
    result = await resume_roasting_service.roast_resume(
        resume_text=test_resume,
        style="funny"
    )
    
    return {
        "message": "LangChain integration test successful",
        "langchain_status": "available",  # Always available as required dependency
        "langsmith_status": langsmith_status,
        "result": result
    }

@router.get("/langsmith-status")
async def check_langsmith_status():
    """
    Check LangSmith configuration and tracing status (no auth required)
    
    Returns:
        dict: LangSmith configuration status
    """
    status = resume_roasting_service.verify_langsmith_setup()
    
    return {
        "langsmith_configuration": status,
        "recommendations": {
            "tracing_url": "https://smith.langchain.com",
            "project_name": "faltuai-fun",
            "next_steps": [
                "Verify LANGCHAIN_API_KEY in environment",
                "Check LangSmith dashboard for traces",
                "Ensure project 'faltuai-fun' exists in LangSmith"
            ]
        }
    }

@router.get("/demo")
async def demo_roast(current_user: User = Depends(get_current_active_user)):
    """
    Demo endpoint showing example resume roasting
    
    Returns:
        dict: Demo roasting example
    """
    demo_resume = """
    John Doe
    Email: john@example.com
    
    Experience:
    - Worked at company for 2 years
    - Did stuff
    - Made things better
    
    Skills:
    - Microsoft Office
    - Good communication
    - Team player
    """
    
    result = await resume_roasting_service.roast_resume(
        resume_text=demo_resume,
        style="funny"
    )
    
    return {
        "demo_resume": demo_resume,
        "roasting_result": result,
        "message": "This is a demo of how resume roasting works!"
    }

@router.get("/history")
async def get_user_roast_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
    offset: int = 0
):
    """
    Get user's resume roasting history
    
    Args:
        current_user: Authenticated user
        db: Database session
        limit: Number of sessions to retrieve (default: 10, max: 50)
        offset: Offset for pagination (default: 0)
        
    Returns:
        dict: List of roasting sessions with metadata
    """
    try:
        # Validate limit
        if limit > 50:
            limit = 50
            
        # Get user's roasting history
        sessions = await ResumeRoastDatabaseService.get_user_roast_history(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        # Get total count for pagination
        total_count = await ResumeRoastDatabaseService.get_user_roast_count(
            db=db,
            user_id=current_user.id
        )
        
        # Format response
        session_list = []
        for session in sessions:
            session_data = {
                "id": session.id,
                "roast_style": session.roast_style,
                "original_filename": session.original_filename,
                "file_type": session.file_type,
                "roast_result": session.roast_result,
                "suggestions": session.suggestions,
                "confidence_score": session.confidence_score,
                "processing_time_ms": session.processing_time_ms,
                "created_at": session.created_at.isoformat(),
                "resume_text_preview": session.resume_text[:200] + "..." if len(session.resume_text) > 200 else session.resume_text
            }
            session_list.append(session_data)
        
        return {
            "sessions": session_list,
            "pagination": {
                "total": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "message": f"Retrieved {len(session_list)} roasting sessions"
        }
        
    except Exception as e:
        logger.error(f"Error getting user roast history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roasting history. Please try again."
        )

@router.get("/history/{session_id}")
async def get_roast_session_details(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed information about a specific roasting session
    
    Args:
        session_id: ID of the roasting session
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Detailed session information
    """
    try:
        # Get session details (with user verification)
        session = await ResumeRoastDatabaseService.get_roast_session_by_id(
            db=db,
            session_id=session_id,
            user_id=current_user.id
        )
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Roasting session not found or you don't have permission to access it"
            )
        
        return {
            "id": session.id,
            "roast_style": session.roast_style,
            "original_filename": session.original_filename,
            "file_type": session.file_type,
            "resume_text": session.resume_text,
            "roast_result": session.roast_result,
            "suggestions": session.suggestions,
            "confidence_score": session.confidence_score,
            "processing_time_ms": session.processing_time_ms,
            "created_at": session.created_at.isoformat(),
            "message": "Session details retrieved successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting roast session details: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve session details. Please try again."
        )

@router.get("/stats")
async def get_user_roasting_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's roasting statistics and activity summary
    
    Args:
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: User statistics and activity summary
    """
    try:
        # Get total roast count
        total_roasts = await ResumeRoastDatabaseService.get_user_roast_count(
            db=db,
            user_id=current_user.id
        )
        
        # Get recent sessions for stats
        recent_sessions = await ResumeRoastDatabaseService.get_user_roast_history(
            db=db,
            user_id=current_user.id,
            limit=100  # Get more for better stats
        )
        
        # Calculate style preferences
        style_counts = {}
        total_processing_time = 0
        processed_count = 0
        
        for session in recent_sessions:
            # Count styles
            style = session.roast_style
            style_counts[style] = style_counts.get(style, 0) + 1
            
            # Calculate average processing time
            if session.processing_time_ms:
                total_processing_time += session.processing_time_ms
                processed_count += 1
        
        avg_processing_time = total_processing_time // processed_count if processed_count > 0 else 0
        
        return {
            "total_roasts": total_roasts,
            "style_preferences": style_counts,
            "average_processing_time_ms": avg_processing_time,
            "account_created": current_user.created_at.isoformat(),
            "last_login": current_user.last_login.isoformat() if current_user.last_login else None,
            "is_premium": current_user.is_premium,
            "message": "User statistics retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"Error getting user roasting stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics. Please try again."
        )

# Export router
__all__ = ["router"]