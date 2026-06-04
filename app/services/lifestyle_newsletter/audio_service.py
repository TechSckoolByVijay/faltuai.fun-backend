"""
Audio Generation Service — wraps ElevenLabs and Deepgram APIs for TTS.

BYOK model: the caller must supply the decrypted API key(s) at call time.
Keys are NEVER stored inside this module.

Supported modes:
  - Single voice (news / newsletter): generates audio from plain text
  - Multi-speaker (podcast): parses "Speaker A:" / "Speaker B:" lines and stitches segments

Fallback logic:
  - If primary provider fails and fallback_enabled=True, automatically retries with secondary
"""
from __future__ import annotations

import logging
import re
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

# Default Deepgram Aura voice used when user hasn't configured one.
# Luna generally sounds calmer/more conversational for newsletter narration.
DEEPGRAM_DEFAULT_VOICE = "aura-luna-en"


# ---------------------------------------------------------------------------
# Markdown stripping — clean up formatting before TTS
# ---------------------------------------------------------------------------

def _strip_markdown(text: str) -> str:
    """Remove markdown syntax so TTS reads naturally."""
    text = re.sub(r"^#{1,6}\s+", "", text, flags=re.MULTILINE)   # headers
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)                  # bold
    text = re.sub(r"\*(.*?)\*", r"\1", text)                      # italic
    text = re.sub(r"^>\s+", "", text, flags=re.MULTILINE)         # blockquotes
    text = re.sub(r"^---+$", "\n", text, flags=re.MULTILINE)      # section dividers
    text = re.sub(r"\[(.*?)\]\(.*?\)", r"\1", text)               # markdown links
    text = re.sub(r"\n{3,}", "\n\n", text)                        # excess blank lines
    return text.strip()


def _prepare_deepgram_text(text: str) -> str:
    """
    Clean and shape text for more natural Deepgram delivery.
    - Removes URL-heavy noise that sounds robotic when spoken
    - Converts hard line breaks to sentence boundaries
    - Adds mild pauses around section boundaries
    """
    text = _strip_markdown(text)
    text = re.sub(r"https?://\S+", "", text)  # do not read raw URLs aloud
    text = re.sub(r"\bSource:\s*[^\n]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bLink:\s*[^\n]+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\bSpeaker\s+[AB]:\s*", "", text, flags=re.IGNORECASE)

    # Make line transitions sound like small pauses
    text = text.replace("\n\n", ".\n\n")
    text = re.sub(r"\n+", ". ", text)

    # Normalize punctuation spacing and repeated separators
    text = re.sub(r"\s{2,}", " ", text)
    text = re.sub(r"\.\s*\.\s*\.", ".", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"([a-zA-Z0-9])\s+-\s+([a-zA-Z0-9])", r"\1, \2", text)

    return text.strip()


# ---------------------------------------------------------------------------
# ElevenLabs
# ---------------------------------------------------------------------------

async def generate_audio_elevenlabs(
    script: str,
    api_key: str,
    voice_id: str,
    model_id: str = "eleven_turbo_v2_5",
) -> Optional[bytes]:
    """Generate single-voice audio via ElevenLabs TTS. Returns raw MP3 bytes."""
    try:
        from elevenlabs import ElevenLabs  # type: ignore

        clean_script = _strip_markdown(script)
        client = ElevenLabs(api_key=api_key)
        audio_gen = client.text_to_speech.convert(
            voice_id=voice_id,
            text=clean_script,
            model_id=model_id,
            output_format="mp3_44100_128",
        )
        audio_bytes = b"".join(audio_gen)
        logger.info("ElevenLabs: generated %d bytes", len(audio_bytes))
        return audio_bytes
    except Exception as exc:
        logger.error("ElevenLabs TTS failed: %s", exc)
        return None


async def generate_podcast_audio_elevenlabs(
    script: str,
    api_key: str,
    voice_a_id: str,
    voice_b_id: str,
    model_id: str = "eleven_turbo_v2_5",
) -> Optional[bytes]:
    """
    Generate multi-speaker podcast audio from a Speaker A/B dialogue script.
    Generates each speaker segment separately then concatenates the MP3 bytes.
    Falls back to single-voice if the script lacks Speaker A/B markers.
    """
    try:
        from elevenlabs import ElevenLabs  # type: ignore

        # Parse "Speaker A: ..." / "Speaker B: ..." lines
        lines = re.findall(
            r"(Speaker [AB]):\s*(.+?)(?=\nSpeaker [AB]:|$)",
            script,
            re.DOTALL,
        )
        if not lines:
            logger.info("Podcast script has no Speaker A/B markers — falling back to single voice")
            return await generate_audio_elevenlabs(script, api_key, voice_a_id, model_id)

        client = ElevenLabs(api_key=api_key)
        segments: list[bytes] = []
        for speaker, text in lines:
            v_id = voice_a_id if speaker == "Speaker A" else voice_b_id
            gen = client.text_to_speech.convert(
                voice_id=v_id,
                text=text.strip(),
                model_id=model_id,
                output_format="mp3_44100_128",
            )
            seg = b"".join(gen)
            segments.append(seg)
            logger.debug("Podcast segment %s: %d bytes", speaker, len(seg))

        combined = b"".join(segments)
        logger.info("Podcast audio: %d segments, %d total bytes", len(segments), len(combined))
        return combined
    except Exception as exc:
        logger.error("ElevenLabs podcast audio failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Deepgram
# ---------------------------------------------------------------------------

def _chunk_text(text: str, max_chars: int = 1900) -> list[str]:
    """
    Split text into chunks of at most max_chars, breaking at sentence boundaries.
    Deepgram has a hard 2000-char limit per request.
    """
    if len(text) <= max_chars:
        return [text]

    chunks: list[str] = []
    # Split on sentence-ending punctuation followed by whitespace
    sentences = re.split(r'(?<=[.!?])\s+', text)
    current = ""
    for sentence in sentences:
        # If a single sentence is too long, hard-split it
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(sentence), max_chars):
                chunks.append(sentence[i:i + max_chars])
            continue
        if len(current) + len(sentence) + 1 > max_chars:
            if current:
                chunks.append(current.strip())
            current = sentence
        else:
            current = (current + " " + sentence).strip() if current else sentence
    if current:
        chunks.append(current.strip())
    return chunks


async def generate_audio_deepgram(
    script: str,
    api_key: str,
    voice_id: str = DEEPGRAM_DEFAULT_VOICE,
) -> Optional[bytes]:
    """
    Generate audio via Deepgram TTS (Aura model family). Returns raw MP3 bytes.
    Automatically chunks the script to respect Deepgram's 2000-char limit.
    """
    try:
        clean_script = _prepare_deepgram_text(script)
        chunks = _chunk_text(clean_script, max_chars=1900)
        url = f"https://api.deepgram.com/v1/speak?model={voice_id}&encoding=mp3"
        headers = {
            "Authorization": f"Token {api_key}",
            "Content-Type": "application/json",
        }
        segments: list[bytes] = []
        async with httpx.AsyncClient(timeout=120.0) as client:
            for i, chunk in enumerate(chunks):
                resp = await client.post(url, headers=headers, json={"text": chunk})
                if resp.status_code != 200:
                    logger.error(
                        "Deepgram TTS HTTP %d on chunk %d/%d: %s",
                        resp.status_code, i + 1, len(chunks), resp.text[:300],
                    )
                    return None
                segments.append(resp.content)
                logger.debug("Deepgram chunk %d/%d: %d bytes", i + 1, len(chunks), len(resp.content))

        audio_bytes = b"".join(segments)
        logger.info("Deepgram: %d chunks, %d total bytes", len(chunks), len(audio_bytes))
        return audio_bytes
    except Exception as exc:
        logger.error("Deepgram TTS failed: %s", exc)
        return None


# ---------------------------------------------------------------------------
# Unified entry point with primary + fallback logic
# ---------------------------------------------------------------------------

async def generate_audio_with_fallback(
    script: str,
    presentation_mode: str = "news",
    elevenlabs_key: Optional[str] = None,
    deepgram_key: Optional[str] = None,
    voice_id: Optional[str] = None,
    audio_provider: str = "elevenlabs",
    fallback_enabled: bool = True,
    secondary_voice_id: Optional[str] = None,
) -> Optional[bytes]:
    """
    Generate audio using the configured provider with optional automatic fallback.

    Provider logic:
      "elevenlabs" → try ElevenLabs; if fails + fallback_enabled, try Deepgram
      "deepgram"   → try Deepgram;   if fails + fallback_enabled, try ElevenLabs
      "both"       → same as "elevenlabs" (ElevenLabs is primary, Deepgram is fallback)

    For presentation_mode="podcast" with ElevenLabs, uses two-voice stitching when
    secondary_voice_id is provided.
    """
    from app.config import settings

    el_voice = voice_id or settings.ELEVENLABS_VOICE_ID
    # Deepgram voices use the "aura-*" naming scheme — never pass an ElevenLabs voice ID to Deepgram
    dg_voice = voice_id if (voice_id and voice_id.startswith("aura-")) else DEEPGRAM_DEFAULT_VOICE

    use_elevenlabs_first = audio_provider in ("elevenlabs", "both")

    if use_elevenlabs_first:
        if elevenlabs_key:
            if presentation_mode == "podcast" and secondary_voice_id:
                audio = await generate_podcast_audio_elevenlabs(
                    script, elevenlabs_key, el_voice, secondary_voice_id
                )
            else:
                audio = await generate_audio_elevenlabs(script, elevenlabs_key, el_voice)
            if audio:
                return audio
            if not fallback_enabled or not deepgram_key:
                logger.warning("ElevenLabs failed and no Deepgram fallback available")
                return None
            logger.warning("ElevenLabs failed — falling back to Deepgram")
            return await generate_audio_deepgram(script, deepgram_key, dg_voice)
        elif deepgram_key:
            # No ElevenLabs key but have Deepgram — use it directly
            return await generate_audio_deepgram(script, deepgram_key, dg_voice)
    else:
        # Deepgram primary
        if deepgram_key:
            audio = await generate_audio_deepgram(script, deepgram_key, dg_voice)
            if audio:
                return audio
            if not fallback_enabled or not elevenlabs_key:
                logger.warning("Deepgram failed and no ElevenLabs fallback available")
                return None
            logger.warning("Deepgram failed — falling back to ElevenLabs")
            return await generate_audio_elevenlabs(script, elevenlabs_key, el_voice)
        elif elevenlabs_key:
            return await generate_audio_elevenlabs(script, elevenlabs_key, el_voice)

    return None


# ---------------------------------------------------------------------------
# Backward-compatible wrapper (used by existing callers)
# ---------------------------------------------------------------------------

async def generate_audio(script: str, api_key: str, voice_id: str) -> Optional[bytes]:
    """Backward-compatible wrapper — delegates to ElevenLabs single-voice."""
    return await generate_audio_elevenlabs(script, api_key, voice_id)


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------

async def save_audio_to_storage(audio_bytes: bytes, episode_id: int) -> Optional[str]:
    """
    Persist audio bytes to storage and return a public URL.
    MVP: saves to /tmp. TODO: replace with Azure Blob Storage.
    """
    import os
    import tempfile

    try:
        tmp_dir = tempfile.gettempdir()
        filename = f"ln_episode_{episode_id}.mp3"
        filepath = os.path.join(tmp_dir, filename)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        audio_url = f"/api/v1/lifestyle-newsletter/audio/{filename}"
        logger.info("AudioService: saved %d bytes to %s", len(audio_bytes), filepath)
        return audio_url
    except Exception as exc:
        logger.error("AudioService: save failed: %s", exc)
        return None

    """
    Convert a text script to audio bytes via ElevenLabs.

    Args:
        script:   The TTS-ready narration script.
        api_key:  User's decrypted ElevenLabs API key (not stored after return).
        voice_id: ElevenLabs voice ID.

    Returns:
        Raw MP3 bytes on success, None on failure.
    """
    try:
        from elevenlabs import ElevenLabs  # type: ignore

        client = ElevenLabs(api_key=api_key)
        audio_generator = client.text_to_speech.convert(
            voice_id=voice_id,
            text=script,
            model_id="eleven_turbo_v2_5",
            output_format="mp3_44100_128",
        )
        # convert generator to bytes
        audio_bytes = b"".join(audio_generator)
        logger.info("AudioGenerationService: generated %d bytes of audio", len(audio_bytes))
        return audio_bytes
    except Exception as exc:
        logger.error("AudioGenerationService: ElevenLabs call failed: %s", exc)
        return None


async def save_audio_to_storage(audio_bytes: bytes, episode_id: int) -> Optional[str]:
    """
    Persist audio bytes to storage and return a public URL.

    MVP implementation: saves to local /tmp and returns a placeholder path.
    TODO: replace with Azure Blob Storage upload when AZURE_STORAGE_CONNECTION_STRING is set.
    """
    import os
    import tempfile

    try:
        tmp_dir = tempfile.gettempdir()
        filename = f"ln_episode_{episode_id}.mp3"
        filepath = os.path.join(tmp_dir, filename)
        with open(filepath, "wb") as f:
            f.write(audio_bytes)
        # In production this would be a CDN / blob URL
        audio_url = f"/api/v1/lifestyle-newsletter/audio/{filename}"
        logger.info("AudioGenerationService: saved audio to %s", filepath)
        return audio_url
    except Exception as exc:
        logger.error("AudioGenerationService: failed to save audio: %s", exc)
        return None
