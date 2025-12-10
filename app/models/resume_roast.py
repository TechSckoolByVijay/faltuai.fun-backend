"""
Resume roasting models for storing roasting history and results
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class ResumeRoastSession(Base):
    """
    Model for storing resume roasting sessions
    """
    __tablename__ = "resume_roast_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    original_filename = Column(String(255), nullable=True)
    file_type = Column(String(50), nullable=True)
    resume_text = Column(Text, nullable=False)
    roast_style = Column(String(50), nullable=False, default="funny")
    roast_result = Column(Text, nullable=False)
    suggestions = Column(JSON, nullable=True)  # Store suggestions as JSON array
    confidence_score = Column(Float, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("User", backref="roast_sessions")
    
    def __repr__(self):
        return f"<ResumeRoastSession(id={self.id}, user_id={self.user_id}, style='{self.roast_style}')>"


class UserActivityLog(Base):
    """
    Model for logging user activity and API usage
    """
    __tablename__ = "user_activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String(100), nullable=False, index=True)  # 'resume_roast', 'login', 'logout', etc.
    endpoint = Column(String(255), nullable=True)  # API endpoint used
    request_data = Column(JSON, nullable=True)  # Store request parameters as JSON
    response_status = Column(String(20), nullable=True)  # 'success', 'error', etc.
    error_message = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv4 and IPv6 support
    user_agent = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationship to user
    user = relationship("User", backref="activity_logs")
    
    def __repr__(self):
        return f"<UserActivityLog(id={self.id}, user_id={self.user_id}, activity='{self.activity_type}')>"


class SystemMetrics(Base):
    """
    Model for storing system-wide metrics and statistics
    """
    __tablename__ = "system_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float, nullable=False)
    metric_unit = Column(String(50), nullable=True)  # 'count', 'ms', 'bytes', etc.
    tags = Column(JSON, nullable=True)  # Additional metadata as JSON
    recorded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<SystemMetrics(id={self.id}, name='{self.metric_name}', value={self.metric_value})>"