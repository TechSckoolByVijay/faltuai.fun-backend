"""
ArXiv Adapter — fetches recent AI research papers using the ArXiv Atom feed API.

Categories fetched:
  cs.AI  — Artificial Intelligence
  cs.LG  — Machine Learning
  cs.CL  — Computation and Language (NLP / LLMs)
  cs.CV  — Computer Vision
  cs.RO  — Robotics

Papers are limited to those submitted within LN_CONTENT_LOOKBACK_DAYS.
The adapter returns a readable abstract so the LLM can reference real findings.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from xml.etree import ElementTree as ET

import httpx

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent
from .base import SourceAdapter

logger = logging.getLogger(__name__)

ARXIV_NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}

ARXIV_QUERY = (
    "cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.CV+OR+cat:cs.RO"
)
ARXIV_API_URL = (
    "https://export.arxiv.org/api/query"
    f"?search_query={ARXIV_QUERY}"
    "&sortBy=submittedDate&sortOrder=descending"
    "&max_results=30"
)


def _parse_arxiv_date(date_str: str) -> datetime | None:
    """Parse ArXiv ISO-8601 date string to timezone-aware datetime."""
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except Exception:
        return None


class ArXivAdapter(SourceAdapter):
    """Fetches recent AI/ML research papers from ArXiv."""

    source_name = "arxiv"

    async def fetch(self) -> List[NormalizedContent]:
        lookback_days = settings.LN_CONTENT_LOOKBACK_DAYS
        cutoff = datetime.now(tz=timezone.utc) - timedelta(days=lookback_days)
        logger.info(
            "ArXivAdapter: lookback=%d days, cutoff=%s",
            lookback_days,
            cutoff.strftime("%Y-%m-%d"),
        )

        items: List[NormalizedContent] = []
        try:
            async with httpx.AsyncClient(timeout=20) as client:
                resp = await client.get(ARXIV_API_URL)
                if resp.status_code != 200:
                    logger.warning("ArXivAdapter: API returned %d", resp.status_code)
                    return items

                root = ET.fromstring(resp.text)
                entries = root.findall("atom:entry", ARXIV_NS)

                for entry in entries:
                    if len(items) >= 8:
                        break

                    # Publication date
                    published_el = entry.find("atom:published", ARXIV_NS)
                    pub_str = published_el.text.strip() if published_el is not None else ""
                    pub_dt = _parse_arxiv_date(pub_str)
                    if pub_dt and pub_dt < cutoff:
                        continue

                    title_el = entry.find("atom:title", ARXIV_NS)
                    title = " ".join((title_el.text or "").split()) if title_el is not None else ""

                    # Abstract — truncate to 500 chars for LLM context
                    summary_el = entry.find("atom:summary", ARXIV_NS)
                    abstract = " ".join((summary_el.text or "").split())[:500] if summary_el is not None else ""

                    # Authors
                    authors = [
                        a.find("atom:name", ARXIV_NS).text
                        for a in entry.findall("atom:author", ARXIV_NS)
                        if a.find("atom:name", ARXIV_NS) is not None
                    ]
                    author_str = ", ".join(authors[:3])
                    if len(authors) > 3:
                        author_str += " et al."

                    # URL — prefer the HTML abstract page
                    url = ""
                    for link in entry.findall("atom:link", ARXIV_NS):
                        if link.get("type") == "text/html":
                            url = link.get("href", "")
                            break
                    if not url:
                        id_el = entry.find("atom:id", ARXIV_NS)
                        url = id_el.text.strip() if id_el is not None else ""

                    # Categories
                    primary_cat = entry.find("arxiv:primary_category", ARXIV_NS)
                    cat_term = primary_cat.get("term", "") if primary_cat is not None else ""

                    arxiv_id = url.split("/abs/")[-1] if "/abs/" in url else ""

                    items.append(
                        NormalizedContent(
                            id=f"arxiv_{arxiv_id}",
                            title=title,
                            summary=abstract or "No abstract available.",
                            source="arxiv.org",
                            url=url,
                            category="research",
                            engagement_score=2.0,  # Papers get a baseline bump
                            author=author_str,
                            timestamp=pub_str,
                            content_type="article",
                            metadata={"arxiv_id": arxiv_id, "category": cat_term},
                        )
                    )

        except Exception as exc:
            logger.warning("ArXivAdapter: failed: %s", exc)

        logger.info("ArXivAdapter: fetched %d papers", len(items))
        return items
