"""
Pydantic schemas for the Lifestyle Newsletter (ln_) feature.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Subscription schemas
# ---------------------------------------------------------------------------

# Default sources available
ALL_SOURCES = ["github", "hackernews", "reddit", "arxiv", "articles", "producthunt"]

TOPIC_SUGGESTIONS = [
    "LLMs", "Agents", "Computer Vision", "Robotics", "Open Source",
    "Startups", "Research Papers", "AI Safety", "Multimodal", "Fine-tuning",
    "RAG", "Embeddings", "Voice AI", "Code Generation", "Reasoning",
]


class LnSubscribeRequest(BaseModel):
    frequency: Literal["daily", "weekly"] = "weekly"
    delivery_time: str = Field(default="08:00", pattern=r"^\d{2}:\d{2}$")
    # User's own API keys — encrypted immediately, never echoed back
    elevenlabs_api_key: Optional[str] = Field(default=None, min_length=10, max_length=200)
    deepgram_api_key: Optional[str] = Field(default=None, min_length=10, max_length=200)
    # Content preferences — all optional; null = use defaults
    topics_follow: Optional[List[str]] = Field(default=None, max_length=20)
    topics_exclude: Optional[List[str]] = Field(default=None, max_length=20)
    sources_enabled: Optional[List[str]] = Field(default=None, max_length=10)
    # Presentation & audio
    presentation_mode: Optional[Literal["news", "podcast"]] = "news"
    audio_provider: Optional[Literal["elevenlabs", "deepgram", "both"]] = "elevenlabs"
    voice_id: Optional[str] = Field(default=None, max_length=200)
    fallback_enabled: Optional[bool] = True
    # Advanced content targeting
    custom_topics: Optional[List[str]] = Field(default=None, max_length=30)
    priority_people: Optional[List[str]] = Field(default=None, max_length=20)

    @field_validator("elevenlabs_api_key", "deepgram_api_key", mode="before")
    @classmethod
    def strip_key(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None

    @field_validator("sources_enabled", mode="before")
    @classmethod
    def validate_sources(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return [s.lower().strip() for s in v if s.lower().strip() in ALL_SOURCES] or None


class LnSubscriptionResponse(BaseModel):
    id: int
    user_id: int
    frequency: str
    delivery_time: Optional[str]
    is_active: bool
    # NEVER return raw keys. Only indicate whether one is saved.
    has_elevenlabs_key: bool
    elevenlabs_key_hint: Optional[str] = None
    has_deepgram_key: bool = False
    deepgram_key_hint: Optional[str] = None
    # Content preferences
    topics_follow: Optional[List[str]] = None
    topics_exclude: Optional[List[str]] = None
    sources_enabled: Optional[List[str]] = None
    # Presentation & audio
    presentation_mode: str = "news"
    audio_provider: str = "elevenlabs"
    voice_id: Optional[str] = None
    fallback_enabled: bool = True
    # Advanced content targeting
    custom_topics: Optional[List[str]] = None
    priority_people: Optional[List[str]] = None
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class LnUpdateKeyRequest(BaseModel):
    """Rotate / remove the ElevenLabs API key for the current user."""
    # Send None / null to remove the key entirely
    elevenlabs_api_key: Optional[str] = Field(default=None, max_length=200)

    @field_validator("elevenlabs_api_key", mode="before")
    @classmethod
    def strip_key(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None


class LnUpdateDeepgramKeyRequest(BaseModel):
    """Rotate / remove the Deepgram API key for the current user."""
    deepgram_api_key: Optional[str] = Field(default=None, max_length=200)

    @field_validator("deepgram_api_key", mode="before")
    @classmethod
    def strip_key(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() if v else None


class LnVoiceInfo(BaseModel):
    """A single TTS voice option returned by the /voices endpoint."""
    voice_id: str
    name: str
    description: Optional[str] = None
    preview_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Podcast episode schemas
# ---------------------------------------------------------------------------

class LnEpisodeResponse(BaseModel):
    id: int
    title: str
    script: Optional[str] = None        # Full script — readable even without audio
    audio_url: Optional[str] = None     # None until audio is generated
    status: str                          # pending | generating | ready | failed
    error_message: Optional[str] = None
    sources_metadata: Optional[List[Dict[str, Any]]] = None
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = {"from_attributes": True}


class LnGenerateRequest(BaseModel):
    """Manual trigger payload."""
    force: bool = False
    sources_override: Optional[List[str]] = Field(
        default=None,
        description="Override which sources to use for this single run. Null = use subscription defaults.",
    )
    lookback_days: Optional[int] = Field(
        default=None,
        ge=1,
        le=90,
        description="How many days back to search for content. Overrides LN_CONTENT_LOOKBACK_DAYS env var for this run.",
    )
    topics_override: Optional[List[str]] = Field(
        default=None,
        description="Override focus topics for this single run. Null = use subscription defaults.",
    )


class LnGenerateResponse(BaseModel):
    message: str
    episode_id: Optional[int] = None
    status: str
    script: Optional[str] = None
    title: Optional[str] = None
    audio_url: Optional[str] = None
    presentation_mode: Optional[Literal["news", "podcast"]] = None


class LnGenerateAudioRequest(BaseModel):
    script: str = Field(..., min_length=10, description="Podcast/news script text to convert to audio")
    voice: Optional[str] = Field(default=None, description="Optional voice/model override")
    episode_id: Optional[int] = Field(default=None, description="Attach generated audio to an existing episode")


class LnGenerateAudioResponse(BaseModel):
    audio_url: str
    episode_id: Optional[int] = None


class LnTopicsRequest(BaseModel):
    """Update saved focus topics."""
    topics_follow: Optional[List[str]] = Field(default=None, description="Topics to prioritise.", max_length=30)
    topics_exclude: Optional[List[str]] = Field(default=None, description="Topics to suppress.", max_length=20)


class LnTopicsResponse(BaseModel):
    """Current saved focus topics."""
    topics_follow: Optional[List[str]] = None
    topics_exclude: Optional[List[str]] = None


# ---------------------------------------------------------------------------
# Normalized content schema (internal — used by adapters and ranking engine)
# ---------------------------------------------------------------------------

class NormalizedContent(BaseModel):
    id: str
    title: str
    summary: str
    source: str
    url: str
    category: Literal["research", "product", "open-source", "trend"]
    engagement_score: float = 0.0
    author: str = ""
    timestamp: str = ""
    content_type: Literal["article", "repo", "post", "video"]
    metadata: Dict[str, Any] = Field(default_factory=dict)
