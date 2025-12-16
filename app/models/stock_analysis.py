"""
Stock Analysis Models
Database models for storing stock fundamental analysis data
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class StockAnalysis(Base):
    """
    Stock Analysis Request and Report Storage
    Stores complete analysis reports for user queries
    """
    __tablename__ = "stock_analyses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Request details
    user_question = Column(Text, nullable=False)  # Original user query
    stock_symbol = Column(String(20), nullable=True, index=True)  # e.g., "RELIANCE", "TCS"
    stock_name = Column(String(255), nullable=True)  # e.g., "Reliance Industries Ltd"
    
    # Analysis results
    analysis_plan = Column(Text, nullable=True)  # The research plan generated
    research_data = Column(Text, nullable=True)  # Raw research data collected
    final_report = Column(Text, nullable=True)  # Complete analysis report
    
    # Metadata
    model_name = Column(String(50), nullable=True)  # LLM model used
    analysis_status = Column(String(20), default="pending", nullable=False)  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)  # Error details if failed
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="stock_analyses")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_created', 'user_id', 'created_at'),
        Index('idx_stock_symbol', 'stock_symbol', 'created_at'),
        Index('idx_status', 'analysis_status'),
    )
    
    def __repr__(self):
        return f"<StockAnalysis(id={self.id}, stock={self.stock_symbol}, user_id={self.user_id}, status={self.analysis_status})>"


class StockAnalysisCache(Base):
    """
    Cache for Stock Analysis Data
    Stores research data to avoid duplicate API calls
    Similar to market_research_cache pattern
    """
    __tablename__ = "stock_analysis_cache"

    id = Column(Integer, primary_key=True, index=True)
    
    # Cache key components
    stock_symbol = Column(String(20), nullable=False, index=True)
    data_type = Column(String(50), nullable=False)  # 'search_data', 'financial_data', 'news', etc.
    query_hash = Column(String(64), nullable=False, index=True)  # Hash of the query for exact matching
    
    # Cached data
    cached_data = Column(Text, nullable=False)  # JSON string of the cached response
    
    # Cache metadata
    is_valid = Column(Boolean, default=True, nullable=False)
    cache_hits = Column(Integer, default=0, nullable=False)  # Track usage
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional expiry
    
    # Indexes for fast lookup
    __table_args__ = (
        Index('idx_cache_lookup', 'stock_symbol', 'data_type', 'query_hash'),
        Index('idx_cache_expiry', 'expires_at', 'is_valid'),
    )
    
    def __repr__(self):
        return f"<StockAnalysisCache(id={self.id}, stock={self.stock_symbol}, type={self.data_type}, hits={self.cache_hits})>"
