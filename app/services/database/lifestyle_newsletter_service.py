"""
Database service for the Lifestyle Newsletter (ln_) feature.
Handles all DB CRUD for ln_subscriptions and ln_podcast_episodes.
"""
from __future__ import annotations

import logging
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lifestyle_newsletter import LnPodcastEpisode, LnSubscription

logger = logging.getLogger(__name__)


class LnDbService:
    # ------------------------------------------------------------------
    # Subscription operations
    # ------------------------------------------------------------------

    @staticmethod
    async def get_subscription(db: AsyncSession, user_id: int) -> Optional[LnSubscription]:
        result = await db.execute(select(LnSubscription).where(LnSubscription.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def upsert_subscription(
        db: AsyncSession,
        user_id: int,
        frequency: str,
        delivery_time: str,
        elevenlabs_key_encrypted: Optional[str],
        topics_follow: Optional[List] = None,
        topics_exclude: Optional[List] = None,
        sources_enabled: Optional[List] = None,
        presentation_mode: Optional[str] = None,
        audio_provider: Optional[str] = None,
        deepgram_key_encrypted: Optional[str] = None,
        voice_id: Optional[str] = None,
        fallback_enabled: Optional[bool] = None,
        custom_topics: Optional[List] = None,
        priority_people: Optional[List] = None,
    ) -> LnSubscription:
        existing = await LnDbService.get_subscription(db, user_id)
        if existing:
            existing.frequency = frequency
            existing.delivery_time = delivery_time
            existing.is_active = True
            if elevenlabs_key_encrypted is not None:
                existing.elevenlabs_api_key_encrypted = elevenlabs_key_encrypted or None
            if deepgram_key_encrypted is not None:
                existing.deepgram_api_key_encrypted = deepgram_key_encrypted or None
            # Update preferences when explicitly passed (None = "don't touch")
            if topics_follow is not None:
                existing.topics_follow = topics_follow or None
            if topics_exclude is not None:
                existing.topics_exclude = topics_exclude or None
            if sources_enabled is not None:
                existing.sources_enabled = sources_enabled or None
            if presentation_mode is not None:
                existing.presentation_mode = presentation_mode
            if audio_provider is not None:
                existing.audio_provider = audio_provider
            if voice_id is not None:
                existing.voice_id = voice_id or None
            if fallback_enabled is not None:
                existing.fallback_enabled = fallback_enabled
            if custom_topics is not None:
                existing.custom_topics = custom_topics or None
            if priority_people is not None:
                existing.priority_people = priority_people or None
            await db.commit()
            await db.refresh(existing)
            return existing

        sub = LnSubscription(
            user_id=user_id,
            frequency=frequency,
            delivery_time=delivery_time,
            is_active=True,
            elevenlabs_api_key_encrypted=elevenlabs_key_encrypted or None,
            deepgram_api_key_encrypted=deepgram_key_encrypted or None,
            topics_follow=topics_follow or None,
            topics_exclude=topics_exclude or None,
            sources_enabled=sources_enabled or None,
            presentation_mode=presentation_mode or "news",
            audio_provider=audio_provider or "elevenlabs",
            voice_id=voice_id or None,
            fallback_enabled=fallback_enabled if fallback_enabled is not None else True,
            custom_topics=custom_topics or None,
            priority_people=priority_people or None,
        )
        db.add(sub)
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_elevenlabs_key(
        db: AsyncSession,
        user_id: int,
        encrypted_key: Optional[str],
    ) -> Optional[LnSubscription]:
        sub = await LnDbService.get_subscription(db, user_id)
        if not sub:
            return None
        sub.elevenlabs_api_key_encrypted = encrypted_key
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_deepgram_key(
        db: AsyncSession,
        user_id: int,
        encrypted_key: Optional[str],
    ) -> Optional[LnSubscription]:
        sub = await LnDbService.get_subscription(db, user_id)
        if not sub:
            return None
        sub.deepgram_api_key_encrypted = encrypted_key
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_topics(
        db: AsyncSession,
        user_id: int,
        topics_follow: Optional[List],
        topics_exclude: Optional[List],
    ) -> Optional[LnSubscription]:
        sub = await LnDbService.get_subscription(db, user_id)
        if not sub:
            return None
        sub.topics_follow = topics_follow or None
        sub.topics_exclude = topics_exclude or None
        await db.commit()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def get_any_active_subscriber_with_key(db: AsyncSession) -> Optional[LnSubscription]:
        """Used by the scheduler to pick one key for global audio generation (MVP)."""
        result = await db.execute(
            select(LnSubscription).where(
                LnSubscription.is_active == True,
                LnSubscription.elevenlabs_api_key_encrypted.is_not(None),
            ).limit(1)
        )
        return result.scalar_one_or_none()

    # ------------------------------------------------------------------
    # Episode operations
    # ------------------------------------------------------------------

    @staticmethod
    async def create_episode(db: AsyncSession) -> LnPodcastEpisode:
        episode = LnPodcastEpisode(title="Generating...", status="pending")
        db.add(episode)
        await db.commit()
        await db.refresh(episode)
        return episode

    @staticmethod
    async def update_episode_status(db: AsyncSession, episode_id: int, status: str) -> None:
        result = await db.execute(select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.status = status
            await db.commit()

    @staticmethod
    async def complete_episode(
        db: AsyncSession,
        episode_id: int,
        title: str,
        script: str,
        audio_url: Optional[str],
        sources_metadata: list,
    ) -> None:
        result = await db.execute(select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.title = title
            episode.script = script
            episode.audio_url = audio_url
            episode.sources_metadata = sources_metadata
            episode.status = "ready"
            episode.error_message = None
            await db.commit()

    @staticmethod
    async def update_episode_audio(db: AsyncSession, episode_id: int, audio_url: str) -> None:
        result = await db.execute(select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.audio_url = audio_url
            await db.commit()

    @staticmethod
    async def update_episode_script_and_audio(
        db: AsyncSession,
        episode_id: int,
        script: str,
        audio_url: str,
    ) -> None:
        result = await db.execute(select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.script = script
            episode.audio_url = audio_url
            await db.commit()

    @staticmethod
    async def fail_episode(db: AsyncSession, episode_id: int, error_message: str) -> None:
        result = await db.execute(select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id))
        episode = result.scalar_one_or_none()
        if episode:
            episode.status = "failed"
            episode.error_message = error_message
            await db.commit()

    @staticmethod
    async def get_latest_ready_episode(db: AsyncSession) -> Optional[LnPodcastEpisode]:
        result = await db.execute(
            select(LnPodcastEpisode)
            .where(LnPodcastEpisode.status == "ready")
            .order_by(LnPodcastEpisode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_past_episodes(
        db: AsyncSession, limit: int = 20, offset: int = 0
    ) -> List[LnPodcastEpisode]:
        """Return ready episodes ordered newest-first, excluding the very latest."""
        result = await db.execute(
            select(LnPodcastEpisode)
            .where(LnPodcastEpisode.status == "ready")
            .order_by(LnPodcastEpisode.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_episode_by_id(db: AsyncSession, episode_id: int) -> Optional[LnPodcastEpisode]:
        result = await db.execute(
            select(LnPodcastEpisode).where(LnPodcastEpisode.id == episode_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_latest_episode_any_status(db: AsyncSession) -> Optional[LnPodcastEpisode]:
        result = await db.execute(
            select(LnPodcastEpisode)
            .order_by(LnPodcastEpisode.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
