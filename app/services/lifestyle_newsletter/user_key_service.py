"""
User Key Service — BYOK (Bring Your Own Key) for ElevenLabs API keys.

Security contract:
  - Raw API keys are NEVER persisted in plaintext.
  - Encryption uses Fernet (AES-128-CBC + HMAC-SHA256) with a server-side
    secret (LN_ENCRYPTION_SECRET env var).
  - The encrypted ciphertext is what lives in ln_subscriptions.elevenlabs_api_key_encrypted.
  - Decryption is only performed at pipeline execution time, within the
    generating coroutine, and the plaintext is NOT stored in memory after use.
  - The raw key is NEVER returned through any API response.
"""
import logging
from typing import Optional

from cryptography.fernet import Fernet, InvalidToken

from app.config import settings

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    """Build a Fernet instance from LN_ENCRYPTION_SECRET.

    Raises ValueError if the secret is missing or invalid so callers get a
    clear error rather than a cryptic cryptography exception.
    """
    secret = settings.LN_ENCRYPTION_SECRET
    if not secret:
        raise ValueError(
            "LN_ENCRYPTION_SECRET is not set. "
            "Generate one with: python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
        )
    try:
        return Fernet(secret.encode() if isinstance(secret, str) else secret)
    except Exception as exc:
        raise ValueError(f"LN_ENCRYPTION_SECRET is invalid: {exc}") from exc


def encrypt_elevenlabs_key(raw_key: str) -> str:
    """Encrypt a raw ElevenLabs API key and return the ciphertext string."""
    f = _get_fernet()
    ciphertext: bytes = f.encrypt(raw_key.encode("utf-8"))
    return ciphertext.decode("utf-8")


def decrypt_elevenlabs_key(ciphertext: str) -> str:
    """Decrypt an encrypted ElevenLabs API key.

    Returns the raw key string. The caller is responsible for not persisting
    the returned value.

    Raises ValueError on decryption failure (tampered / wrong secret).
    """
    f = _get_fernet()
    try:
        raw: bytes = f.decrypt(ciphertext.encode("utf-8"))
        return raw.decode("utf-8")
    except InvalidToken as exc:
        raise ValueError("Failed to decrypt ElevenLabs API key — possibly wrong secret or tampered data.") from exc


def get_key_hint(ciphertext: Optional[str]) -> Optional[str]:
    """Return a safe display hint (last 4 chars of ciphertext) for UI 'key saved' indicator."""
    if not ciphertext:
        return None
    return f"••••{ciphertext[-4:]}"


# ---------------------------------------------------------------------------
# Generic wrappers (used for Deepgram and any future BYOK providers)
# ---------------------------------------------------------------------------

def encrypt_key(raw_key: str) -> str:
    """Encrypt any API key using LN_ENCRYPTION_SECRET. Same implementation as ElevenLabs."""
    return encrypt_elevenlabs_key(raw_key)


def decrypt_key(ciphertext: str) -> str:
    """Decrypt any API key using LN_ENCRYPTION_SECRET. Same implementation as ElevenLabs."""
    return decrypt_elevenlabs_key(ciphertext)


# Deepgram-specific convenience aliases (same crypto, different semantic label)
encrypt_deepgram_key = encrypt_key
decrypt_deepgram_key = decrypt_key
