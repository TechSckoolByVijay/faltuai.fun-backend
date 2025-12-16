"""
Pydantic Schemas for Stock Analysis API
Request and response models for stock fundamental analysis endpoints
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class AnalysisStatus(str, Enum):
    """Stock analysis status enumeration"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class StockAnalysisRequest(BaseModel):
    """
    Request model for initiating stock analysis
    """
    user_question: str = Field(
        ...,
        description="User's investment question or analysis request",
        min_length=3,
        max_length=500,
        example="Should I invest in Reliance Industries for long-term growth?"
    )
    stock_symbol: Optional[str] = Field(
        None,
        description="Stock symbol (optional, will be extracted from question if not provided)",
        max_length=20,
        example="RELIANCE"
    )
    stock_name: Optional[str] = Field(
        None,
        description="Full company name (optional)",
        max_length=255,
        example="Reliance Industries Limited"
    )

    @validator('stock_symbol')
    def uppercase_symbol(cls, v):
        """Convert stock symbol to uppercase"""
        if v and v.strip():
            return v.strip().upper()
        return None

    class Config:
        json_schema_extra = {
            "example": {
                "user_question": "Should I invest in TCS for long-term growth?",
                "stock_symbol": "TCS",
                "stock_name": "Tata Consultancy Services"
            }
        }


class StockAnalysisResponse(BaseModel):
    """
    Response model for stock analysis results
    """
    id: int = Field(..., description="Analysis record ID")
    user_id: int = Field(..., description="User ID who requested the analysis")
    user_question: str = Field(..., description="Original user question")
    stock_symbol: Optional[str] = Field(None, description="Stock symbol analyzed")
    stock_name: Optional[str] = Field(None, description="Company name")
    
    analysis_plan: Optional[str] = Field(None, description="Research plan generated")
    research_data: Optional[str] = Field(None, description="Raw research data collected")
    final_report: Optional[str] = Field(None, description="Complete analysis report")
    
    model_name: Optional[str] = Field(None, description="LLM model used")
    analysis_status: AnalysisStatus = Field(..., description="Current status of analysis")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    
    created_at: datetime = Field(..., description="Analysis creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "user_id": 123,
                "user_question": "Should I invest in TCS?",
                "stock_symbol": "TCS",
                "stock_name": "Tata Consultancy Services",
                "analysis_status": "completed",
                "final_report": "# TCS Investment Analysis\n\n...",
                "model_name": "gpt-4o-mini",
                "created_at": "2025-12-16T10:00:00Z",
                "updated_at": "2025-12-16T10:05:00Z",
                "completed_at": "2025-12-16T10:05:00Z"
            }
        }


class StockAnalysisSummary(BaseModel):
    """
    Summary model for listing analyses (without full report)
    """
    id: int
    user_question: str
    stock_symbol: Optional[str]
    stock_name: Optional[str]
    analysis_status: AnalysisStatus
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class AnalysisHistoryResponse(BaseModel):
    """
    Response model for user's analysis history
    """
    total: int = Field(..., description="Total number of analyses")
    analyses: List[StockAnalysisSummary] = Field(..., description="List of analyses")

    class Config:
        json_schema_extra = {
            "example": {
                "total": 5,
                "analyses": [
                    {
                        "id": 1,
                        "user_question": "Should I invest in TCS?",
                        "stock_symbol": "TCS",
                        "stock_name": "Tata Consultancy Services",
                        "analysis_status": "completed",
                        "created_at": "2025-12-16T10:00:00Z",
                        "completed_at": "2025-12-16T10:05:00Z"
                    }
                ]
            }
        }


class CacheStatsResponse(BaseModel):
    """
    Response model for cache statistics
    """
    total_entries: int = Field(..., description="Total cache entries")
    valid_entries: int = Field(..., description="Valid cache entries")
    total_hits: int = Field(..., description="Total cache hits")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_entries": 100,
                "valid_entries": 85,
                "total_hits": 1250
            }
        }


class ErrorResponse(BaseModel):
    """
    Standard error response model
    """
    detail: str = Field(..., description="Error message")
    error_code: Optional[str] = Field(None, description="Error code for debugging")
    
    class Config:
        json_schema_extra = {
            "example": {
                "detail": "Stock analysis not found",
                "error_code": "ANALYSIS_NOT_FOUND"
            }
        }
