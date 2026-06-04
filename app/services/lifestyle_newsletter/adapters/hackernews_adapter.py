"""
Hacker News Adapter — fetches AI-related top stories from Hacker News.

Uses the official HN Firebase API (no key required).
For each story it scrapes the actual linked article to extract real content
so the LLM pipeline has genuine facts to work with (not just titles).
"""
from __future__ import annotations

import hashlib
import logging
from typing import List, Optional

import time
from datetime import datetime, timedelta, timezone

import httpx
from bs4 import BeautifulSoup

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

HN_TOP_STORIES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
HN_ITEM_URL = "https://hacker-news.firebaseio.com/v0/item/{}.json"

AI_KEYWORDS = {
    "ai", "llm", "gpt", "openai", "anthropic", "gemini", "mistral", "machine learning",
    "deep learning", "neural", "transformer", "diffusion", "langchain", "langgraph",
    "hugging face", "pytorch", "tensorflow", "generative", "reinforcement", "agents",
    "claude", "copilot", "stable diffusion", "midjourney", "multimodal", "rag",
    "fine-tun", "embedding", "vector", "inference", "benchmark", "model",
}


def _is_ai_related(title: str) -> bool:
    lower = title.lower()
    return any(kw in lower for kw in AI_KEYWORDS)


async def _scrape_article_text(url: str, client: httpx.AsyncClient, max_chars: int = 800) -> str:
    """Fetch the article URL and extract the first meaningful paragraph text."""
    try:
        resp = await client.get(url, timeout=10, follow_redirects=True,
                                headers={"User-Agent": "Mozilla/5.0 (compatible; FaltuAI/1.0)"})
        if resp.status_code != 200:
            return ""
        soup = BeautifulSoup(resp.text, "html.parser")
        # Remove noise tags
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        # Try article/main body first, fall back to <p> tags
        body = soup.find("article") or soup.find("main") or soup
        paragraphs = body.find_all("p")
        text = " ".join(p.get_text(separator=" ", strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 60)
        return text[:max_chars].strip()
    except Exception as exc:
        logger.debug("Article scrape failed for %s: %s", url, exc)
        return ""


class HackerNewsAdapter(SourceAdapter):
    """Fetches top AI-related HN stories with real article content."""

    source_name = "hackernews"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = settings.LN_CONTENT_LOOKBACK_DAYS
        cutoff_ts = int((datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)).timestamp())
        logger.info("HackerNewsAdapter: lookback=%d days, cutoff=%s", lookback_days,
                    datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).strftime("%Y-%m-%d"))
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(HN_TOP_STORIES_URL)
                resp.raise_for_status()
                top_ids: List[int] = resp.json()[:200]  # scan top 200 to find enough within window

                items: List[NormalizedContent] = []
                for story_id in top_ids:
                    if len(items) >= 6:
                        break
                    item_resp = await client.get(HN_ITEM_URL.format(story_id))
                    if item_resp.status_code != 200:
                        continue
                    story = item_resp.json()
                    if not story or story.get("type") != "story":
                        continue
                    # Enforce lookback window using Unix timestamp
                    story_time = story.get("time", 0)
                    if story_time and story_time < cutoff_ts:
                        continue
                    title: str = story.get("title", "")
                    if not _is_ai_related(title):
                        continue

                    story_url: Optional[str] = story.get("url")
                    hn_url = f"https://news.ycombinator.com/item?id={story_id}"
                    url = story_url or hn_url
                    uid = hashlib.md5(url.encode()).hexdigest()
                    score = float(story.get("score", 0))
                    comments = int(story.get("descendants", 0))

                    # Scrape actual article content
                    article_text = ""
                    if story_url:
                        article_text = await _scrape_article_text(story_url, client)

                    if article_text:
                        summary = article_text
                    else:
                        summary = (
                            f"HN trending story with {score:.0f} points and {comments} comments. "
                            f"Discussion: {hn_url}"
                        )

                    items.append(
                        NormalizedContent(
                            id=f"hn_{uid}",
                            title=title,
                            summary=summary,
                            source="hackernews",
                            url=url,
                            category="trend",
                            engagement_score=score + comments * 0.5,
                            author=story.get("by", ""),
                            timestamp=str(story.get("time", "")),
                            content_type="article",
                            metadata={"hn_score": score, "comments": comments, "hn_id": story_id,
                                      "has_real_content": bool(article_text)},
                        )
                    )
        except Exception as exc:
            logger.warning("HackerNewsAdapter fetch failed: %s", exc)
            return []

        logger.info("HackerNewsAdapter: fetched %d items", len(items))
        return items
