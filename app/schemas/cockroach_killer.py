from pydantic import BaseModel, Field
from typing import List, Optional


class CockroachScoreRequest(BaseModel):
    score: int = Field(..., ge=0, description='Final score from the game')
    player_name: str = Field(..., min_length=1, max_length=255, description='Player display name')
    theme: str = Field(..., description='Selected game theme')


class CockroachScoreResponse(BaseModel):
    message: str
    score: int
    best_score: int
    plays: int
    title: str


class CockroachLeaderboardEntry(BaseModel):
    user_id: int
    player_name: Optional[str]
    email: str
    best_score: int
    total_plays: int


class CockroachLeaderboardResponse(BaseModel):
    entries: List[CockroachLeaderboardEntry]


class CockroachUserStatsResponse(BaseModel):
    plays: int
    best_score: int
    last_score: int


__all__ = [
    'CockroachScoreRequest',
    'CockroachScoreResponse',
    'CockroachLeaderboardEntry',
    'CockroachLeaderboardResponse',
    'CockroachUserStatsResponse',
]
