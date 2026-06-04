"""
Articles Adapter — scrapes AI-related news articles from curated RSS feeds
and optionally extracts YouTube video transcripts embedded in articles.

YouTube transcript retrieval uses youtube-transcript-api (no key required).
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import List, Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

# Curated AI-focused RSS/Atom feeds
CURATED_FEEDS = [
    "https://feeds.feedburner.com/oreilly/radar/atom",        # O'Reilly Radar
    "https://blog.openai.com/rss/",                           # OpenAI Blog
    "https://www.deeplearning.ai/the-batch/feed/",            # DeepLearning.AI The Batch
    "https://huggingface.co/blog/feed.xml",                   # HuggingFace Blog
]

YOUTUBE_EMBED_PATTERN = re.compile(
    r'(?:youtube\.com/(?:embed/|watch\?v=)|youtu\.be/)([A-Za-z0-9_-]{11})'
)


def _extract_youtube_ids(html: str) -> List[str]:
    return list(set(YOUTUBE_EMBED_PATTERN.findall(html)))


async def _get_youtube_transcript(video_id: str, max_duration_minutes: int = 15) -> Optional[str]:
    """Attempt to fetch a YouTube transcript. Returns compressed text or None."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi  # type: ignore
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en"])
        # Estimate duration
        if transcript_list:
            last = transcript_list[-1]
            duration_min = (last["start"] + last.get("duration", 0)) / 60
            if duration_min > max_duration_minutes:
                return None
        text = " ".join(t["text"] for t in transcript_list)
        # Trim to ~2000 chars for LLM processing
        return text[:2000]
    except Exception as exc:
        logger.debug("YouTube transcript fetch failed for %s: %s", video_id, exc)
        return None


def _parse_entry_date(entry) -> Optional[datetime]:
    """Try to extract a publish date from an RSS <item> or Atom <entry>."""
    for tag_name in ("pubDate", "published", "updated", "dc:date"):
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


async def _parse_feed(feed_url: str, client: httpx.AsyncClient, cutoff: datetime) -> List[NormalizedContent]:
    """Minimal RSS/Atom parser — returns items published within the lookback window."""
    items: List[NormalizedContent] = []
    try:
        resp = await client.get(feed_url, timeout=15, follow_redirects=True)
        if resp.status_code != 200:
            return items
        soup = BeautifulSoup(resp.text, "html.parser")
        # Support both RSS <item> and Atom <entry>
        entries = soup.find_all("item") or soup.find_all("entry")
        for entry in entries[:20]:  # scan more, but filter by date
            title_tag = entry.find("title")
            link_tag = entry.find("link")
            summary_tag = entry.find("summary") or entry.find("description")

            title = title_tag.get_text(strip=True) if title_tag else ""
            url = (
                link_tag.get("href") or link_tag.get_text(strip=True)
                if link_tag else ""
            )
            raw_summary = summary_tag.get_text(strip=True)[:500] if summary_tag else ""

            # Date filter
            pub_date = _parse_entry_date(entry)
            if pub_date and pub_date < cutoff:
                continue  # too old
            pub_iso = pub_date.isoformat() if pub_date else ""

            if not title or not url:
                continue

            # Check for embedded YouTube videos
            full_html = str(entry)
            yt_ids = _extract_youtube_ids(full_html)
            extra_metadata: dict = {}
            if yt_ids:
                transcript = await _get_youtube_transcript(yt_ids[0])
                if transcript:
                    extra_metadata["youtube_transcript"] = transcript
                    extra_metadata["youtube_video_id"] = yt_ids[0]
                    logger.info("Extracted YouTube transcript for %s", yt_ids[0])

            uid = hashlib.md5(url.encode()).hexdigest()
            domain = urlparse(feed_url).netloc.replace("www.", "")

            items.append(
                NormalizedContent(
                    id=f"art_{uid}",
                    title=title,
                    summary=raw_summary or "No summary available.",
                    source=domain,
                    url=url,
                    category="research",
                    engagement_score=1.0,
                    author="",
                    timestamp=pub_iso,
                    content_type="video" if yt_ids else "article",
                    metadata=extra_metadata,
                )
            )
            if len(items) >= 5:
                break
    except Exception as exc:
        logger.warning("ArticlesAdapter feed parse failed for %s: %s", feed_url, exc)
    return items


class ArticlesAdapter(SourceAdapter):
    """Fetches AI articles from curated RSS/Atom feeds within the lookback window."""

    source_name = "articles"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = settings.LN_CONTENT_LOOKBACK_DAYS
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
        logger.info("ArticlesAdapter: lookback=%d days, cutoff=%s", lookback_days, cutoff.strftime("%Y-%m-%d"))
        async with httpx.AsyncClient(timeout=20) as client:
            all_items: List[NormalizedContent] = []
            for feed_url in CURATED_FEEDS:
                try:
                    items = await _parse_feed(feed_url, client, cutoff)
                    logger.info("  Feed %s → %d items within window", feed_url, len(items))
                    all_items.extend(items)
                except Exception as exc:
                    logger.warning("ArticlesAdapter feed failed %s: %s", feed_url, exc)
            return all_items
