"""
GitHub Trending Adapter — fetches trending AI repositories from GitHub.

Uses the GitHub Search API (no key required for basic use; optional GITHUB_TOKEN
for higher rate limits).
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import List

import httpx

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

GITHUB_SEARCH_URL = "https://api.github.com/search/repositories"
AI_QUERY = "artificial intelligence OR machine learning OR LLM OR large language model OR generative AI"


class GitHubAdapter(SourceAdapter):
    """Fetches trending AI repositories created or updated in the last N days."""

    source_name = "github"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = settings.LN_CONTENT_LOOKBACK_DAYS
        since_date = (datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        headers = {"Accept": "application/vnd.github.v3+json"}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"

        params = {
            "q": f"{AI_QUERY} stars:>100 pushed:>{since_date}",
            "sort": "stars",
            "order": "desc",
            "per_page": 20,
        }

        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(GITHUB_SEARCH_URL, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            logger.warning("GitHubAdapter fetch failed: %s", exc)
            return []

        items: List[NormalizedContent] = []
        for repo in data.get("items", []):
            desc = repo.get("description") or ""
            if len(desc.strip()) < 20:
                continue  # skip repos with no real description
            uid = hashlib.md5(repo["html_url"].encode()).hexdigest()
            items.append(
                NormalizedContent(
                    id=f"gh_{uid}",
                    title=repo.get("full_name", ""),
                    summary=repo.get("description") or "No description provided.",
                    source="github",
                    url=repo.get("html_url", ""),
                    category="open-source",
                    engagement_score=float(repo.get("stargazers_count", 0)),
                    author=repo.get("owner", {}).get("login", ""),
                    timestamp=repo.get("pushed_at", ""),
                    content_type="repo",
                    metadata={
                        "stars": repo.get("stargazers_count", 0),
                        "forks": repo.get("forks_count", 0),
                        "language": repo.get("language", ""),
                        "topics": repo.get("topics", []),
                    },
                )
            )

        logger.info("GitHubAdapter: fetched %d items", len(items))
        return items
