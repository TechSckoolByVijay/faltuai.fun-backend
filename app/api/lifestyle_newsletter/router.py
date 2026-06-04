"""
Lifestyle Newsletter API Router.

Endpoints:
  GET  /lifestyle-newsletter/health
  POST /lifestyle-newsletter/subscribe          — upsert subscription + optional BYOK key
  GET  /lifestyle-newsletter/subscription       — get current user's subscription status
  PUT  /lifestyle-newsletter/api-key            — rotate / remove ElevenLabs key
  GET  /lifestyle-newsletter/podcast/latest     — latest episode (script always; audio if key saved)
  POST /lifestyle-newsletter/generate           — manual trigger (admin / debug)
  GET  /lifestyle-newsletter/audio/{filename}   — serve local audio file (MVP, pre-blob-storage)
"""
import logging
import os
import tempfile
from pathlib import Path
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.schemas.lifestyle_newsletter import (
    LnEpisodeResponse,
    LnGenerateAudioRequest,
    LnGenerateAudioResponse,
    LnGenerateRequest,
    LnGenerateResponse,
    LnSubscribeRequest,
    LnSubscriptionResponse,
    LnTopicsRequest,
    LnTopicsResponse,
    LnUpdateDeepgramKeyRequest,
    LnUpdateKeyRequest,
)
from app.schemas.user import User
from app.services.database.lifestyle_newsletter_service import LnDbService
from app.services.lifestyle_newsletter import progress_store as ps
from app.services.lifestyle_newsletter.user_key_service import (
    encrypt_elevenlabs_key,
    encrypt_key,
    decrypt_elevenlabs_key,
    decrypt_key,
    get_key_hint,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/lifestyle-newsletter", tags=["Lifestyle Newsletter"])


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _subscription_to_response(sub) -> LnSubscriptionResponse:
    return LnSubscriptionResponse(
        id=sub.id,
        user_id=sub.user_id,
        frequency=sub.frequency,
        delivery_time=sub.delivery_time,
        is_active=sub.is_active,
        has_elevenlabs_key=bool(sub.elevenlabs_api_key_encrypted),
        elevenlabs_key_hint=get_key_hint(sub.elevenlabs_api_key_encrypted),
        has_deepgram_key=bool(sub.deepgram_api_key_encrypted),
        deepgram_key_hint=get_key_hint(sub.deepgram_api_key_encrypted),
        topics_follow=sub.topics_follow,
        topics_exclude=sub.topics_exclude,
        sources_enabled=sub.sources_enabled,
        presentation_mode=sub.presentation_mode or "news",
        audio_provider=sub.audio_provider or "elevenlabs",
        voice_id=sub.voice_id,
        fallback_enabled=sub.fallback_enabled if sub.fallback_enabled is not None else True,
        custom_topics=sub.custom_topics,
        priority_people=sub.priority_people,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/health")
async def health():
    return {"status": "ok", "feature": "lifestyle-newsletter"}


@router.post("/subscribe", response_model=LnSubscriptionResponse, status_code=status.HTTP_200_OK)
async def subscribe(
    payload: LnSubscribeRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Subscribe (or update subscription) to the AI Audio Newsletter.
    Optionally pass an ElevenLabs API key — it is encrypted immediately
    and the raw key is never persisted or returned.
    """
    encrypted_key = None
    if payload.elevenlabs_api_key:
        try:
            encrypted_key = encrypt_elevenlabs_key(payload.elevenlabs_api_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Key encryption failed — LN_ENCRYPTION_SECRET may not be configured: {exc}",
            )

    encrypted_dg_key = None
    if payload.deepgram_api_key:
        try:
            encrypted_dg_key = encrypt_key(payload.deepgram_api_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deepgram key encryption failed: {exc}",
            )

    sub = await LnDbService.upsert_subscription(
        db=db,
        user_id=current_user.id,
        frequency=payload.frequency,
        delivery_time=payload.delivery_time,
        elevenlabs_key_encrypted=encrypted_key,
        deepgram_key_encrypted=encrypted_dg_key,
        topics_follow=payload.topics_follow,
        topics_exclude=payload.topics_exclude,
        sources_enabled=payload.sources_enabled,
        presentation_mode=payload.presentation_mode,
        audio_provider=payload.audio_provider,
        voice_id=payload.voice_id,
        fallback_enabled=payload.fallback_enabled,
        custom_topics=payload.custom_topics,
        priority_people=payload.priority_people,
    )
    return _subscription_to_response(sub)


@router.get("/subscription", response_model=LnSubscriptionResponse)
async def get_subscription(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the current user's subscription details."""
    sub = await LnDbService.get_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No subscription found.")
    return _subscription_to_response(sub)


@router.put("/api-key", response_model=LnSubscriptionResponse)
async def update_api_key(
    payload: LnUpdateKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate or remove the user's ElevenLabs API key.

    - Send a new key string to update (encrypted on write).
    - Send null / empty string to remove the key entirely.
    - The raw key is NEVER returned in any response.
    """
    encrypted_key: str | None = None
    if payload.elevenlabs_api_key:
        try:
            encrypted_key = encrypt_elevenlabs_key(payload.elevenlabs_api_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Key encryption failed: {exc}",
            )
    # If None is sent, we clear the stored key
    sub = await LnDbService.update_elevenlabs_key(db, current_user.id, encrypted_key)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found. Subscribe first before managing your key.",
        )
    return _subscription_to_response(sub)


@router.put("/deepgram-key", response_model=LnSubscriptionResponse)
async def update_deepgram_key(
    payload: LnUpdateDeepgramKeyRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Rotate or remove the user's Deepgram API key.
    Send null / empty string to remove the key entirely.
    """
    encrypted_key: str | None = None
    if payload.deepgram_api_key:
        try:
            encrypted_key = encrypt_key(payload.deepgram_api_key)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Deepgram key encryption failed: {exc}",
            )
    sub = await LnDbService.update_deepgram_key(db, current_user.id, encrypted_key)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found. Subscribe first before managing your key.",
        )
    return _subscription_to_response(sub)


@router.get("/voices")
async def get_voices(
    provider: str = "elevenlabs",
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return available TTS voices for the given provider.
    - ElevenLabs: dynamically fetched using the user's saved key.
    - Deepgram: static list of Aura voice models.
    """
    if provider == "deepgram":
        return [
            {"voice_id": "aura-asteria-en",  "name": "Asteria (Female, US)"},
            {"voice_id": "aura-luna-en",     "name": "Luna (Female, US)"},
            {"voice_id": "aura-stella-en",   "name": "Stella (Female, US)"},
            {"voice_id": "aura-athena-en",   "name": "Athena (Female, UK)"},
            {"voice_id": "aura-hera-en",     "name": "Hera (Female, US)"},
            {"voice_id": "aura-orion-en",    "name": "Orion (Male, US)"},
            {"voice_id": "aura-arcas-en",    "name": "Arcas (Male, US)"},
            {"voice_id": "aura-perseus-en",  "name": "Perseus (Male, US)"},
            {"voice_id": "aura-angus-en",    "name": "Angus (Male, Irish)"},
            {"voice_id": "aura-orpheus-en",  "name": "Orpheus (Male, US)"},
            {"voice_id": "aura-helios-en",   "name": "Helios (Male, UK)"},
            {"voice_id": "aura-zeus-en",     "name": "Zeus (Male, US)"},
        ]

    if provider == "elevenlabs":
        sub = await LnDbService.get_subscription(db, current_user.id)
        if not sub or not sub.elevenlabs_api_key_encrypted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ElevenLabs key saved. Add your key first.",
            )
        try:
            raw_key = decrypt_elevenlabs_key(sub.elevenlabs_api_key_encrypted)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(
                    "https://api.elevenlabs.io/v1/voices",
                    headers={"xi-api-key": raw_key},
                )
            del raw_key
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ElevenLabs voices API unreachable: {exc}",
            )
        if resp.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=f"ElevenLabs voices API returned {resp.status_code}",
            )
        data = resp.json()
        return [
            {"voice_id": v["voice_id"], "name": v["name"]}
            for v in data.get("voices", [])
        ]

    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Unknown provider: {provider}")


@router.get("/podcast/latest", response_model=LnEpisodeResponse)
async def get_latest_podcast(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return the latest podcast episode.
    - script is always available (readable without audio).
    - audio_url is populated only when the episode was generated with audio.
    """
    episode = await LnDbService.get_latest_ready_episode(db)
    if not episode:
        # Check if one is in progress
        any_ep = await LnDbService.get_latest_episode_any_status(db)
        if any_ep and any_ep.status in ("pending", "generating"):
            return LnEpisodeResponse(
                id=any_ep.id,
                title="Episode is being generated...",
                script=None,
                audio_url=None,
                status=any_ep.status,
                created_at=any_ep.created_at,
                updated_at=any_ep.updated_at,
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No podcast episode available yet. Check back soon or trigger generation manually.",
        )
    return LnEpisodeResponse(
        id=episode.id,
        title=episode.title,
        script=episode.script,
        audio_url=episode.audio_url,
        status=episode.status,
        sources_metadata=episode.sources_metadata,
        created_at=episode.created_at,
        updated_at=episode.updated_at,
    )


@router.post("/generate", response_model=LnGenerateResponse)
async def generate_podcast(
    payload: LnGenerateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Manual step-1 generation: create content/script only.
    Audio is generated explicitly via POST /generate-audio.
    """
    from app.services.lifestyle_newsletter.worker import run_pipeline_for_episode

    sub = await LnDbService.get_subscription(db, current_user.id)
    encrypted_key = sub.elevenlabs_api_key_encrypted if sub else None
    presentation_mode = sub.presentation_mode if sub else "news"
    user_prefs = {
        "topics_follow": payload.topics_override or (sub.topics_follow if sub else None),
        "topics_exclude": sub.topics_exclude if sub else None,
        "sources_enabled": payload.sources_override or (sub.sources_enabled if sub else None),
        "lookback_days": payload.lookback_days,
        "custom_topics": sub.custom_topics if sub else None,
        "priority_people": sub.priority_people if sub else None,
        "presentation_mode": presentation_mode,
        "audio_provider": sub.audio_provider if sub else "elevenlabs",
        "deepgram_key_encrypted": sub.deepgram_api_key_encrypted if sub else None,
        "voice_id": sub.voice_id if sub else None,
        "fallback_enabled": sub.fallback_enabled if sub else True,
    }

    episode = await LnDbService.create_episode(db)
    await run_pipeline_for_episode(
        db=db,
        episode_id=episode.id,
        elevenlabs_key_encrypted=encrypted_key,
        user_prefs=user_prefs,
        generate_audio=False,
    )

    fresh = await LnDbService.get_episode_by_id(db, episode.id)
    if not fresh:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Episode not found after generation")
    if fresh.status == "failed":
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=fresh.error_message or "Generation failed")

    return LnGenerateResponse(
        message="Content generated. Review/edit script and trigger audio when ready.",
        episode_id=fresh.id,
        status=fresh.status,
        script=fresh.script,
        title=fresh.title,
        audio_url=fresh.audio_url,
        presentation_mode=presentation_mode,
    )


@router.get("/episode/{episode_id}/progress")
async def get_episode_progress(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return in-memory live progress messages for a generating episode.
    Also returns the current DB status so the frontend knows when to stop polling.
    """
    # Verify episode exists
    episode = await LnDbService.get_episode_by_id(db, episode_id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")

    messages = ps.get(episode_id)
    return {
        "episode_id": episode_id,
        "status": episode.status,
        "messages": messages,
    }


@router.get("/episodes", response_model=List[LnEpisodeResponse])
async def list_episodes(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Return all ready episodes, newest first.
    Used by the frontend history panel.
    """
    episodes = await LnDbService.get_past_episodes(db, limit=min(limit, 50), offset=offset)
    return [LnEpisodeResponse.model_validate(ep) for ep in episodes]


async def _generate_audio_internal(
    db: AsyncSession,
    current_user: User,
    script: str,
    episode_id: Optional[int] = None,
    voice: Optional[str] = None,
) -> LnGenerateAudioResponse:
    from app.services.lifestyle_newsletter.audio_service import generate_audio_with_fallback, save_audio_to_storage

    sub = await LnDbService.get_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No subscription found. Subscribe first.")

    encrypted_el = sub.elevenlabs_api_key_encrypted
    encrypted_dg = sub.deepgram_api_key_encrypted
    if not encrypted_el and not encrypted_dg:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No audio API key saved. Add an ElevenLabs or Deepgram key in Subscription settings first.",
        )

    clean_script = (script or "").strip()
    if not clean_script:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Script is required")

    from app.services.lifestyle_newsletter.user_key_service import decrypt_elevenlabs_key, decrypt_key
    raw_el = decrypt_elevenlabs_key(encrypted_el) if encrypted_el else None
    raw_dg = decrypt_key(encrypted_dg) if encrypted_dg else None
    audio_bytes = await generate_audio_with_fallback(
        script=clean_script,
        presentation_mode=sub.presentation_mode or "news",
        elevenlabs_key=raw_el,
        deepgram_key=raw_dg,
        voice_id=voice or sub.voice_id,
        audio_provider=sub.audio_provider or "elevenlabs",
        fallback_enabled=sub.fallback_enabled if sub.fallback_enabled is not None else True,
    )
    del raw_el, raw_dg

    if not audio_bytes:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Audio generation returned empty output")

    target_episode_id = episode_id
    if not target_episode_id:
        latest = await LnDbService.get_latest_ready_episode(db)
        if not latest:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No episode found to attach audio")
        target_episode_id = latest.id

    audio_url = await save_audio_to_storage(audio_bytes, target_episode_id)
    if not audio_url:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to save generated audio")

    await LnDbService.update_episode_script_and_audio(db, target_episode_id, clean_script, audio_url)
    return LnGenerateAudioResponse(audio_url=audio_url, episode_id=target_episode_id)


@router.post("/generate-audio", response_model=LnGenerateAudioResponse)
async def generate_audio(
    payload: LnGenerateAudioRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Manual step-2 endpoint: generate audio from user-edited script text."""
    return await _generate_audio_internal(
        db=db,
        current_user=current_user,
        script=payload.script,
        episode_id=payload.episode_id,
        voice=payload.voice,
    )


@router.post("/episode/{episode_id}/generate-audio", response_model=LnGenerateResponse)
async def generate_audio_for_episode(
    episode_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible route for legacy clients."""
    episode = await LnDbService.get_episode_by_id(db, episode_id)
    if not episode:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Episode not found.")
    if not episode.script:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Episode has no script to narrate.")

    result = await _generate_audio_internal(
        db=db,
        current_user=current_user,
        script=episode.script,
        episode_id=episode_id,
        voice=None,
    )
    return LnGenerateResponse(
        message="Audio generated successfully.",
        episode_id=result.episode_id,
        status="ready",
        audio_url=result.audio_url,
    )


@router.get("/audio/{filename}")
async def serve_audio(
    filename: str,
    token: Optional[str] = None,
    request: Request = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Serve locally stored audio files (MVP — pre-Azure Blob Storage).
    Accepts auth via Bearer header OR ?token= query param (needed for <audio> tags).
    """
    from app.auth.tokens import token_manager
    from app.services.database.user_service import UserService

    resolved_token = token
    if not resolved_token and request is not None:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.lower().startswith("bearer "):
            resolved_token = auth_header.split(" ", 1)[1].strip()

    if not resolved_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="token required")

    payload = token_manager.verify_token(resolved_token)
    if not payload:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = await UserService.get_user_by_email(db, payload.get("sub", ""))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Sanitize: only allow ln_episode_*.mp3
    if not filename.startswith("ln_episode_") or not filename.endswith(".mp3"):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid filename.")

    filepath = Path(tempfile.gettempdir()) / filename
    if not filepath.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Audio file not found.")

    return FileResponse(path=str(filepath), media_type="audio/mpeg", filename=filename)


@router.get("/topics", response_model=LnTopicsResponse)
async def get_topics(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Return the current user's saved focus topics."""
    sub = await LnDbService.get_subscription(db, current_user.id)
    if not sub:
        return LnTopicsResponse()
    return LnTopicsResponse(topics_follow=sub.topics_follow, topics_exclude=sub.topics_exclude)


@router.put("/topics", response_model=LnTopicsResponse)
async def update_topics(
    payload: LnTopicsRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Save / update the current user's focus topics."""
    sub = await LnDbService.get_subscription(db, current_user.id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found. Subscribe first before updating topics.",
        )
    updated = await LnDbService.update_topics(
        db, current_user.id,
        topics_follow=payload.topics_follow,
        topics_exclude=payload.topics_exclude,
    )
    return LnTopicsResponse(
        topics_follow=updated.topics_follow,
        topics_exclude=updated.topics_exclude,
    )
