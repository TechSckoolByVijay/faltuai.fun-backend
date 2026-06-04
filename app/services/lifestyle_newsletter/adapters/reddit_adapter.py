"""
Reddit Adapter — fetches top AI posts from curated subreddits using Reddit's
public JSON API (no authentication required for public subreddits).

Subreddits: r/MachineLearning, r/LocalLLaMA, r/artificial, r/singularity
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

SUBREDDITS = [
    "ChatGPT",
    "LocalLLaMA",
    "artificial",
    "singularity",
]

# Keywords that signal off-topic, NSFW, or low-quality posts
BLOCKLIST_TERMS = [
    "nsfw", "porn", "sex", "nude", "naked", "jailbreak", "uncensored bypass",
    "girlfriend", "waifu", "hentai", "gore", "suicide", "self-harm",
    "meme", "shitpost", "rant", "unpopular opinion",
]


def _is_blocked(title: str, flair: str) -> bool:
    combined = (title + " " + flair).lower()
    return any(term in combined for term in BLOCKLIST_TERMS)

# Reddit public JSON endpoint — no auth, but needs a browser-like User-Agent
REDDIT_HEADERS = {
    "User-Agent": "FaltuAI-Newsletter/1.0 (AI weekly briefing bot; educational use)",
    "Accept": "application/json",
}


class RedditAdapter(SourceAdapter):
    """Fetches trending AI discussions from curated subreddits."""

    source_name = "reddit"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = settings.LN_CONTENT_LOOKBACK_DAYS
        cutoff_ts = int(
            (datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)).timestamp()
        )
        logger.info(
            "RedditAdapter: lookback=%d days, cutoff=%s",
            lookback_days,
            datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).strftime("%Y-%m-%d"),
        )

        items: List[NormalizedContent] = []
        async with httpx.AsyncClient(timeout=15, headers=REDDIT_HEADERS) as client:
            for sub in SUBREDDITS:
                if len(items) >= 15:
                    break
                try:
                    url = f"https://www.reddit.com/r/{sub}/top.json?t=week&limit=25"
                    resp = await client.get(url)
                    if resp.status_code != 200:
                        logger.warning("RedditAdapter: %s returned %d", sub, resp.status_code)
                        continue

                    data = resp.json()
                    posts = data.get("data", {}).get("children", [])

                    for post in posts:
                        p = post.get("data", {})
                        created = p.get("created_utc", 0)
                        if created and created < cutoff_ts:
                            continue

                        title: str = p.get("title", "").strip()
                        score: int = p.get("score", 0)
                        num_comments: int = p.get("num_comments", 0)
                        permalink: str = p.get("permalink", "")
                        full_url = (
                            p.get("url") or f"https://reddit.com{permalink}"
                        )
                        selftext: str = (p.get("selftext") or "").strip()[:600]
                        flair: str = p.get("link_flair_text") or ""

                        # Skip NSFW, off-topic, or low-quality posts
                        if p.get("over_18") or _is_blocked(title, flair):
                            logger.debug("RedditAdapter: blocked post '%s'", title[:60])
                            continue

                        # Prefer posts with real content or meaningful discussion
                        if score < 50 and num_comments < 10:
                            continue

                        summary = selftext if selftext and len(selftext) > 80 else (
                            f"r/{sub} post with {score} upvotes and {num_comments} comments. {flair}"
                        ).strip()

                        pub_iso = (
                            datetime.fromtimestamp(created, tz=timezone.utc).isoformat()
                            if created else ""
                        )

                        items.append(
                            NormalizedContent(
                                id=f"reddit_{p.get('id', '')}",
                                title=title,
                                summary=summary,
                                source=f"reddit/r/{sub}",
                                url=full_url,
                                category="trend",
                                engagement_score=float(score + num_comments * 3),
                                author=p.get("author", ""),
                                timestamp=pub_iso,
                                content_type="article",
                                metadata={
                                    "subreddit": sub,
                                    "score": score,
                                    "num_comments": num_comments,
                                    "flair": flair,
                                },
                            )
                        )

                        if len(items) >= 15:
                            break

                except Exception as exc:
                    logger.warning("RedditAdapter: subreddit %s failed: %s", sub, exc)

        logger.info("RedditAdapter: fetched %d items", len(items))
        return items
