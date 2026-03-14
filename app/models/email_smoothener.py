"""
Email Smoothener models.
"""
from sqlalchemy import Column, Integer, Text, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class EmailSmoothenerSession(Base):
    """
    Stores Email Smoothener generation sessions.
    Table uses feature prefix `esm_` for discoverability.
    """

    __tablename__ = "esm_email_smoothener_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    raw_text = Column(Text, nullable=False)
    result_json = Column(JSON, nullable=False)
    processing_time_ms = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", backref="esm_email_smoothener_sessions")

    def __repr__(self):
        return f"<EmailSmoothenerSession(id={self.id}, user_id={self.user_id})>"
