"""
FastAPI Router for Stock Analysis
Handles all stock fundamental analysis endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request
from fastapi.exceptions import RequestValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
from datetime import datetime

# Local imports
from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.stock_analysis import (
    StockAnalysisRequest,
    StockAnalysisResponse,
    StockAnalysisSummary,
    AnalysisHistoryResponse,
    ErrorResponse,
    AnalysisStatus
)
from app.services.stock_analysis_service import stock_analysis_service
from app.services.database.stock_analysis_service import stock_analysis_db_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/stock-analysis", tags=["Stock Analysis"])


@router.post("/analyze", response_model=StockAnalysisResponse, status_code=202)
async def create_stock_analysis(
    raw_request: Request,
    request: StockAnalysisRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new stock fundamental analysis
    
    **Process:**
    1. Creates analysis record in database
    2. Triggers background analysis workflow
    3. Returns analysis ID immediately
    4. Client can poll for results using GET /stock-analysis/{analysis_id}
    
    **Analysis includes:**
    - Executive Summary & Recommendation
    - Company Overview & Business Model
    - Industry & Macro Analysis
    - Financial Analysis (Historical)
    - Valuation & Projections
    - Core Risks & Monitoring Indicators
    - ESG Considerations
    """
    try:
        body = await raw_request.json()
        logger.info(f"Raw request body: {body}")
    except:
        pass
    
    logger.info(f"Stock analysis request received: question='{request.user_question}', symbol={request.stock_symbol}, name={request.stock_name}")
    
    try:
        # Create analysis record
        analysis = await stock_analysis_db_service.create_analysis(
            db=db,
            user_id=current_user.id,
            user_question=request.user_question,
            stock_symbol=request.stock_symbol,
            stock_name=request.stock_name
        )
        
        # Trigger background analysis
        background_tasks.add_task(
            run_analysis_workflow,
            analysis_id=analysis.id,
            user_question=request.user_question,
            stock_symbol=request.stock_symbol,
            stock_name=request.stock_name
        )
        
        logger.info(f"Started stock analysis {analysis.id} for user {current_user.id}")
        
        return StockAnalysisResponse.model_validate(analysis)
        
    except Exception as e:
        logger.error(f"Error creating stock analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create analysis: {str(e)}")


async def run_analysis_workflow(
    analysis_id: int,
    user_question: str,
    stock_symbol: Optional[str] = None,
    stock_name: Optional[str] = None
):
    """
    Background task to run the complete analysis workflow
    """
    from app.core.database import AsyncSessionLocal
    
    async with AsyncSessionLocal() as db:
        try:
            # Update status to processing
            await stock_analysis_db_service.update_analysis(
                db=db,
                analysis_id=analysis_id,
                analysis_status=AnalysisStatus.PROCESSING.value
            )
            
            # Run LangGraph analysis
            result = await stock_analysis_service.run_analysis(
                user_question=user_question,
                stock_symbol=stock_symbol,
                stock_name=stock_name
            )
            
            # Check for errors
            if result.get("error"):
                await stock_analysis_db_service.update_analysis(
                    db=db,
                    analysis_id=analysis_id,
                    analysis_status=AnalysisStatus.FAILED.value,
                    error_message=result["error"]
                )
                logger.error(f"Analysis {analysis_id} failed: {result['error']}")
                return
            
            # Update with results
            await stock_analysis_db_service.update_analysis(
                db=db,
                analysis_id=analysis_id,
                analysis_plan=result.get("analysis_plan"),
                research_data=result.get("research_data"),
                final_report=result.get("final_report"),
                model_name=result.get("model"),
                analysis_status=AnalysisStatus.COMPLETED.value,
                completed_at=datetime.utcnow()
            )
            
            logger.info(f"Analysis {analysis_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Error in analysis workflow {analysis_id}: {e}")
            await stock_analysis_db_service.update_analysis(
                db=db,
                analysis_id=analysis_id,
                analysis_status=AnalysisStatus.FAILED.value,
                error_message=str(e)
            )


@router.get("/analyze/{analysis_id}", response_model=StockAnalysisResponse)
async def get_stock_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get stock analysis by ID
    
    Returns the complete analysis including report if completed
    """
    try:
        analysis = await stock_analysis_db_service.get_analysis_by_id(
            db=db,
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or you don't have permission to access it"
            )
        
        return StockAnalysisResponse.model_validate(analysis)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve analysis: {str(e)}")


@router.get("/history", response_model=AnalysisHistoryResponse)
async def get_analysis_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user's stock analysis history
    
    Returns a paginated list of analyses ordered by creation date (newest first)
    """
    try:
        analyses = await stock_analysis_db_service.get_user_analyses(
            db=db,
            user_id=current_user.id,
            limit=limit,
            offset=offset
        )
        
        summaries = [StockAnalysisSummary.model_validate(a) for a in analyses]
        
        return AnalysisHistoryResponse(
            total=len(summaries),
            analyses=summaries
        )
        
    except Exception as e:
        logger.error(f"Error getting analysis history for user {current_user.id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")


@router.get("/stock/{stock_symbol}", response_model=List[StockAnalysisSummary])
async def get_analyses_by_stock(
    stock_symbol: str,
    limit: int = 10,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all completed analyses for a specific stock symbol
    
    Useful for viewing historical analyses of the same company
    """
    try:
        analyses = await stock_analysis_db_service.get_analyses_by_stock(
            db=db,
            stock_symbol=stock_symbol,
            user_id=current_user.id,
            limit=limit
        )
        
        return [StockAnalysisSummary.model_validate(a) for a in analyses]
        
    except Exception as e:
        logger.error(f"Error getting analyses for stock {stock_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve stock analyses: {str(e)}")


@router.delete("/analyze/{analysis_id}", status_code=204)
async def delete_analysis(
    analysis_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a stock analysis
    
    Only the user who created the analysis can delete it
    """
    try:
        analysis = await stock_analysis_db_service.get_analysis_by_id(
            db=db,
            analysis_id=analysis_id,
            user_id=current_user.id
        )
        
        if not analysis:
            raise HTTPException(
                status_code=404,
                detail="Analysis not found or you don't have permission to delete it"
            )
        
        await db.delete(analysis)
        await db.commit()
        
        logger.info(f"Deleted analysis {analysis_id} for user {current_user.id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting analysis {analysis_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete analysis: {str(e)}")


@router.post("/cache/invalidate/{stock_symbol}", status_code=200)
async def invalidate_stock_cache(
    stock_symbol: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Invalidate cached data for a specific stock
    
    Useful when fresh data is needed for a new analysis
    Requires authentication but doesn't check ownership
    """
    try:
        count = await stock_analysis_db_service.invalidate_cache(
            db=db,
            stock_symbol=stock_symbol
        )
        
        logger.info(f"Invalidated {count} cache entries for {stock_symbol}")
        
        return {"message": f"Invalidated {count} cache entries for {stock_symbol}"}
        
    except Exception as e:
        logger.error(f"Error invalidating cache for {stock_symbol}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to invalidate cache: {str(e)}")
