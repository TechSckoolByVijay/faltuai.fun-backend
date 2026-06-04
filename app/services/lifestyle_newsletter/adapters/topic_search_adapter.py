"""
TopicSearchAdapter — uses the Serper.dev Google Search API to actively find
recent news/content about user-specified focus topics (e.g. "Elon Musk",
"Sam Altman", "Grok").

This runs ONLY when the user has set focus topics. For each topic it fires
a targeted Google search scoped to the last 7 days and trusted AI/tech
sources, then normalises the results into NormalizedContent items.

If SERPER_API_KEY is not configured, this adapter silently returns [].
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Optional

import httpx

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent

logger = logging.getLogger(__name__)

SERPER_URL = "https://google.serper.dev/news"

# Trusted sources to prioritise in queries (keeps results high signal)
TRUSTED_SOURCES = (
    "site:techcrunch.com OR site:theverge.com OR site:wired.com "
    "OR site:venturebeat.com OR site:arstechnica.com "
    "OR site:reuters.com OR site:bloomberg.com "
    "OR site:news.ycombinator.com OR site:reddit.com "
    "OR site:openai.com OR site:anthropic.com OR site:deepmind.google"
)

# Max results to fetch per topic (keep cost low, quality high)
MAX_RESULTS_PER_TOPIC = 5
# Minimum snippet length to bother including
MIN_SNIPPET_LEN = 60


def _make_query(topic: str) -> str:
    """Build a targeted news query for a topic."""
    return f'"{topic}" AI {TRUSTED_SOURCES}'


def _item_id(topic: str, url: str) -> str:
    return "ts_" + hashlib.md5(f"{topic}:{url}".encode()).hexdigest()[:12]


def _guess_category(title: str, snippet: str) -> str:
    combined = (title + " " + snippet).lower()
    if any(w in combined for w in ["paper", "research", "study", "arxiv", "model", "benchmark"]):
        return "research"
    if any(w in combined for w in ["launch", "release", "product", "tool", "app", "startup"]):
        return "product"
    if any(w in combined for w in ["github", "open source", "repo", "library", "framework"]):
        return "open-source"
    return "trend"


async def fetch_topic_news(
    topics: List[str],
    lookback_days: int = 7,
) -> List[NormalizedContent]:
    """
    Search for each focus topic using Serper Google News API.
    Returns a deduplicated list of NormalizedContent items, all tagged
    source='topic_search' so the LLM knows these are user-requested.

    Silently returns [] if:
    - SERPER_API_KEY is not set
    - The API call fails for any reason
    """
    if not settings.SERPER_API_KEY:
        logger.info("TopicSearch: SERPER_API_KEY not set — skipping topic search")
        return []

    if not topics:
        return []

    # Map lookback_days → Serper tbs (time-based search) parameter
    if lookback_days <= 1:
        tbs = "qdr:d"
    elif lookback_days <= 7:
        tbs = "qdr:w"
    elif lookback_days <= 30:
        tbs = "qdr:m"
    else:
        tbs = "qdr:y"

    headers = {
        "X-API-KEY": settings.SERPER_API_KEY,
        "Content-Type": "application/json",
    }

    all_items: List[NormalizedContent] = []
    seen_urls: set = set()

    async with httpx.AsyncClient(timeout=15) as client:
        for topic in topics:
            try:
                query = _make_query(topic)
                payload = {
                    "q": query,
                    "num": MAX_RESULTS_PER_TOPIC,
                    "tbs": tbs,
                }
                resp = await client.post(SERPER_URL, headers=headers, json=payload)
                resp.raise_for_status()
                data = resp.json()

                news_items = data.get("news", [])
                logger.info(
                    "TopicSearch: topic='%s' → %d results from Serper",
                    topic, len(news_items)
                )

                for item in news_items:
                    url = item.get("link", "")
                    title = item.get("title", "").strip()
                    snippet = item.get("snippet", "").strip()
                    source = item.get("source", "web")
                    date_str = item.get("date", "")

                    if not url or not title:
                        continue
                    if url in seen_urls:
                        continue
                    if len(snippet) < MIN_SNIPPET_LEN:
                        continue

                    seen_urls.add(url)

                    # Build a rich summary: snippet + context about which topic surfaced it
                    summary = (
                        f"{snippet}\n\n"
                        f"[Found via topic search for: {topic}]"
                    )

                    all_items.append(NormalizedContent(
                        id=_item_id(topic, url),
                        title=title,
                        summary=summary,
                        source="topic_search",
                        url=url,
                        category=_guess_category(title, snippet),
                        engagement_score=80.0,  # Boost: user explicitly asked for this
                        author=source,
                        timestamp=date_str or datetime.now(timezone.utc).isoformat(),
                        content_type="article",
                        metadata={"topic": topic, "search_source": source},
                    ))

            except Exception as exc:
                logger.warning("TopicSearch: failed for topic '%s': %s", topic, exc)
                continue

    logger.info("TopicSearch: collected %d items across %d topics", len(all_items), len(topics))
    return all_items
