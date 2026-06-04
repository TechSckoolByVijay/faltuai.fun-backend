"""
Lifestyle Newsletter models.
Tables use feature prefix `ln_` for discoverability.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Boolean, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base


class LnPodcastEpisode(Base):
    """
    Stores generated podcast episodes (shared globally across subscribers).
    Each episode holds the script, audio URL, and source metadata.
    Table: ln_podcast_episodes
    """
    __tablename__ = "ln_podcast_episodes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(300), nullable=False)
    script = Column(Text, nullable=True)           # Full narration script
    audio_url = Column(Text, nullable=True)        # URL to stored audio file
    sources_metadata = Column(JSON, nullable=True) # List of NormalizedContent dicts used
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending | generating | ready | failed
    error_message = Column(Text, nullable=True)    # Populated on failure
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    def __repr__(self):
        return f"<LnPodcastEpisode(id={self.id}, status={self.status}, title={self.title!r})>"


class LnSubscription(Base):
    """
    Per-user subscription preferences for the Lifestyle Newsletter feature.
    Stores the user's ElevenLabs API key encrypted at rest (BYOK model).
    Decryption happens only during pipeline execution for that user's session.
    Table: ln_subscriptions
    """
    __tablename__ = "ln_subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # one subscription per user
        index=True,
    )
    frequency = Column(String(10), nullable=False, default="weekly")  # daily | weekly
    delivery_time = Column(String(5), nullable=True, default="08:00")  # HH:MM
    is_active = Column(Boolean, nullable=False, default=True)

    # BYOK: user's ElevenLabs API key encrypted via Fernet(LN_ENCRYPTION_SECRET).
    # The raw key is NEVER stored in plaintext. Set to NULL when user removes their key.
    elevenlabs_api_key_encrypted = Column(Text, nullable=True)

    # User content preferences (all nullable = use defaults when unset)
    topics_follow = Column(JSON, nullable=True)    # e.g. ["LLM", "agents", "vision"]
    topics_exclude = Column(JSON, nullable=True)   # e.g. ["crypto", "NFT"]
    sources_enabled = Column(JSON, nullable=True)  # e.g. ["github","hackernews","reddit","arxiv","articles"]

    # Presentation & audio preferences
    presentation_mode = Column(String(20), nullable=False, default="news")  # news | podcast
    audio_provider = Column(String(20), nullable=False, default="elevenlabs")  # elevenlabs | deepgram | both
    deepgram_api_key_encrypted = Column(Text, nullable=True)   # Fernet-encrypted Deepgram key
    voice_id = Column(String(200), nullable=True)              # Voice ID for primary provider
    fallback_enabled = Column(Boolean, nullable=False, default=True)  # Auto-switch on failure

    # Advanced content targeting
    custom_topics = Column(JSON, nullable=True)   # Free-text topics, e.g. ["LangGraph updates"]
    priority_people = Column(JSON, nullable=True) # Names to boost, e.g. ["Andrej Karpathy"]

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    user = relationship("User", backref="ln_subscription")

    def __repr__(self):
        return f"<LnSubscription(id={self.id}, user_id={self.user_id}, frequency={self.frequency})>"
