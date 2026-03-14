from pydantic import BaseModel, Field
from typing import List


class EmailSmoothenerRequest(BaseModel):
    raw_text: str = Field(..., min_length=10, max_length=5000)


class EmailSmoothenerVariant(BaseModel):
    style_key: str
    style_label: str
    smoothed_email: str
    ghosting_probability: int = Field(..., ge=0, le=100)


class EmailDraftAssessment(BaseModel):
    clarity_score: int = Field(..., ge=0, le=100)
    politeness_score: int = Field(..., ge=0, le=100)
    formality_score: int = Field(..., ge=0, le=100)
    tone_summary: str
    sounds_aggressive: bool
    sounds_friendly: bool
    is_good_enough: bool
    good_enough_message: str


class EmailSmoothenerResponse(BaseModel):
    overall_vibe: str
    draft_assessment: EmailDraftAssessment
    variants: List[EmailSmoothenerVariant]


class EmailSmoothenerSessionResponse(BaseModel):
    id: int
    user_id: int
    raw_text: str
    result_json: dict
    processing_time_ms: int | None = None

    class Config:
        from_attributes = True
