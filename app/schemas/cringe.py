from pydantic import BaseModel, Field
from typing import List


class CringeRequest(BaseModel):
    content: str = Field(..., min_length=10, description="Raw LinkedIn post text")


class CringeResponse(BaseModel):
    cringe_score: int = Field(..., ge=0, le=100)
    buzzwords_detected: List[str] = Field(default_factory=list)
    human_rewrite: str
    roast_verdict: str
