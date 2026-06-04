"""
Cockroach Killer score tracking model
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class CockroachKillRecord(Base):
    """Persistent record for Cockroach Killer user plays."""
    __tablename__ = 'cockroach_killer_records'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False, index=True)
    score = Column(Integer, nullable=False)
    player_name = Column(String(255), nullable=False)
    theme = Column(String(100), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship('User', backref='cockroach_killer_records')

    def __repr__(self):
        return f"<CockroachKillRecord(id={self.id}, user_id={self.user_id}, score={self.score})>"
