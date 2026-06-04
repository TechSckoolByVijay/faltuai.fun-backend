"""
Product Hunt Adapter — fetches top AI/tech product launches from the
Product Hunt RSS feed (no API key required).

We filter for products that mention AI, ML, LLM, GPT, automation or
similar keywords so the newsletter's "Top AI Products" section is relevant.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

PRODUCTHUNT_RSS = "https://www.producthunt.com/feed"

# Keywords used to filter AI-relevant products
AI_KEYWORDS = [
    "ai", "artificial intelligence", "machine learning", "ml", "llm", "gpt",
    "claude", "gemini", "openai", "copilot", "automation", "automate", "workflow",
    "chatbot", "chat bot", "agent", "agentic", "generative", "diffusion",
    "image generation", "voice", "tts", "speech", "transcri", "summarize",
    "summarise", "vector", "embedding", "rag", "semantic", "nlp",
    "no-code", "nocode", "productivity", "writing assistant", "coding assistant",
]

# Maximum number of products to include
MAX_PRODUCTS = 8


def _is_ai_relevant(title: str, description: str) -> bool:
    combined = (title + " " + description).lower()
    return any(kw in combined for kw in AI_KEYWORDS)


def _parse_pub_date(entry) -> Optional[datetime]:
    for tag_name in ("pubDate", "published", "updated"):
        tag = entry.find(tag_name)
        if tag:
            raw = tag.get_text(strip=True)
            try:
                return parsedate_to_datetime(raw).replace(tzinfo=timezone.utc)
            except Exception:
                pass
            try:
                return datetime.fromisoformat(raw.replace("Z", "+00:00"))
            except Exception:
                pass
    return None


def _strip_html(html: str) -> str:
    return BeautifulSoup(html, "html.parser").get_text(separator=" ", strip=True)


class ProductHuntAdapter(SourceAdapter):
    source_name = "producthunt"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = getattr(settings, "LN_CONTENT_LOOKBACK_DAYS", 7)
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                resp = await client.get(PRODUCTHUNT_RSS, headers={"User-Agent": "FaltooAI-Newsletter/1.0"})
                resp.raise_for_status()
        except Exception as exc:
            logger.warning("ProductHuntAdapter: RSS fetch failed: %s", exc)
            return []

        soup = BeautifulSoup(resp.text, "html.parser")
        items = soup.find_all("item")
        if not items:
            # Atom-style fallback
            items = soup.find_all("entry")

        results: List[NormalizedContent] = []
        for entry in items:
            try:
                title_tag = entry.find("title")
                link_tag  = entry.find("link")
                desc_tag  = entry.find("description") or entry.find("summary")

                title = title_tag.get_text(strip=True) if title_tag else ""
                url   = (link_tag.get_text(strip=True) if link_tag else
                         link_tag.get("href", "") if link_tag else "")
                raw_desc = desc_tag.get_text(strip=True) if desc_tag else ""
                description = _strip_html(raw_desc)[:800]

                if not title or not url:
                    continue

                # Date filter
                pub_date = _parse_pub_date(entry)
                if pub_date and pub_date < cutoff:
                    continue

                # AI relevance filter
                if not _is_ai_relevant(title, description):
                    continue

                # Engagement: try to grab upvote count from description text
                vote_match = re.search(r"(\d[\d,]+)\s*(?:vote|upvote|point)", description, re.I)
                engagement = float(vote_match.group(1).replace(",", "")) if vote_match else 50.0

                import hashlib as _hl
                _uid = _hl.md5(url.encode()).hexdigest()
                pub_iso = pub_date.isoformat() if pub_date else ""
                results.append(NormalizedContent(
                    id=f"ph_{_uid}",
                    source="producthunt",
                    category="product",
                    title=title,
                    url=url,
                    summary=description or f"AI product launch: {title}",
                    engagement_score=engagement,
                    timestamp=pub_iso,
                    content_type="article",
                ))

                if len(results) >= MAX_PRODUCTS:
                    break

            except Exception as exc:
                logger.debug("ProductHuntAdapter: error parsing entry: %s", exc)
                continue

        logger.info("ProductHuntAdapter: found %d AI-relevant products", len(results))
        return results
