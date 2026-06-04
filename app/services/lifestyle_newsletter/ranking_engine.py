"""
Ranking Engine — filters and scores NormalizedContent items to select
the top N stories for the newsletter episode.

Key design decisions:
  1. Engagement is normalised PER SOURCE (not globally) so a Reddit post with
     400 upvotes is not crushed by an HN story with 400 points.
  2. A hard MAX_PER_SOURCE cap prevents any single source from flooding the feed.
  3. Sources are also given target representation slots so minority sources
     (ArXiv, ProductHunt, Blogs) always get at least 1-2 items.

Scoring formula (all components normalised to [0, 1]):
  score = W_RECENCY * recency
        + W_ENGAGEMENT * engagement_within_source
        + W_SOURCE * source_credibility
        + cross_source_bonus
"""
from __future__ import annotations

import logging
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Dict, List

from app.config import settings
from app.schemas.lifestyle_newsletter import NormalizedContent

logger = logging.getLogger(__name__)

# Scoring weights
W_RECENCY    = 0.30
W_ENGAGEMENT = 0.35
W_SOURCE     = 0.20
W_CROSS      = 0.15

# Maximum items any single source can contribute to the final selection
# (prevents HN from taking all 10 slots)
MAX_PER_SOURCE = 3

# Guaranteed minimum slots per source IF enough items are available.
# Sources not listed here get no guaranteed slot (pure merit).
MIN_SLOTS: Dict[str, int] = {
    "hackernews":  2,
    "reddit":      2,
    "arxiv":       2,
    "github":      2,
    "producthunt": 1,
    "articles":    1,
}

# Source credibility scores (0.0 – 1.0)
SOURCE_CREDIBILITY: Dict[str, float] = {
    "github":      0.85,
    "hackernews":  0.80,
    "reddit":      0.72,
    "arxiv":       0.90,
    "producthunt": 0.75,
    "articles":    0.78,
    "openai.com":  1.00,
    "deeplearning.ai": 0.90,
    "huggingface.co":  0.90,
}


def _recency_score(timestamp_str: str, lookback_days: int) -> float:
    """Returns 1.0 for now, linearly decaying to 0.0 at lookback_days ago."""
    if not timestamp_str:
        return 0.5
    try:
        ts = datetime.fromtimestamp(int(timestamp_str), tz=timezone.utc)
    except (ValueError, OSError):
        try:
            ts = datetime.fromisoformat(timestamp_str.rstrip("Z"))
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
        except Exception:
            return 0.5
    now = datetime.now(tz=timezone.utc)
    age_seconds = (now - ts).total_seconds()
    window_seconds = lookback_days * 86_400
    return max(0.0, 1.0 - age_seconds / window_seconds)


def _source_key(item: NormalizedContent) -> str:
    """Normalise source name to top-level key for grouping and caps."""
    src = item.source.lower()
    for key in SOURCE_CREDIBILITY:
        if key in src:
            return key
    return src.split("/")[0]  # e.g. "reddit/r/MachineLearning" → "reddit"


def _source_credibility(item: NormalizedContent) -> float:
    for key, val in SOURCE_CREDIBILITY.items():
        if key in item.source.lower() or key in item.url.lower():
            return val
    return 0.55


def rank(items: List[NormalizedContent]) -> List[NormalizedContent]:
    """
    1. De-duplicate by URL.
    2. Normalise engagement score within each source group (0–1).
    3. Compute total score per item.
    4. Apply MIN_SLOTS guarantee (pick best from each source first).
    5. Fill remaining slots by global score, respecting MAX_PER_SOURCE cap.
    """
    lookback = settings.LN_CONTENT_LOOKBACK_DAYS
    top_n    = settings.LN_TOP_STORIES_COUNT

    # --- Step 1: De-duplicate by URL ---
    seen_urls: set[str] = set()
    unique: List[NormalizedContent] = []
    for item in items:
        if item.url not in seen_urls:
            seen_urls.add(item.url)
            unique.append(item)

    if not unique:
        return []

    # --- Step 2: Per-source engagement normalisation ---
    source_groups: Dict[str, List[NormalizedContent]] = defaultdict(list)
    for item in unique:
        source_groups[_source_key(item)].append(item)

    # Map item → normalised engagement (0–1 within its source bucket)
    norm_engagement: Dict[str, float] = {}
    for src, grp in source_groups.items():
        max_e = max(i.engagement_score for i in grp) or 1.0
        for i in grp:
            norm_engagement[i.url] = i.engagement_score / max_e

    # Cross-source bonus: same title in 2+ sources
    title_counts: Dict[str, int] = {}
    for item in unique:
        k = item.title.lower()[:80]
        title_counts[k] = title_counts.get(k, 0) + 1

    # --- Step 3: Score every item ---
    def _score(item: NormalizedContent) -> float:
        r = _recency_score(item.timestamp, lookback)
        e = norm_engagement.get(item.url, 0.5)
        s = _source_credibility(item)
        c = W_CROSS if title_counts.get(item.title.lower()[:80], 0) > 1 else 0.0
        return W_RECENCY * r + W_ENGAGEMENT * e + W_SOURCE * s + c

    scored = sorted(unique, key=_score, reverse=True)

    # --- Step 4: MIN_SLOTS guarantee — pick the best item from each source ---
    selected: List[NormalizedContent] = []
    selected_urls: set[str] = set()
    source_counts: Dict[str, int] = defaultdict(int)

    # Guaranteed slots first
    for src, min_n in MIN_SLOTS.items():
        candidates = [i for i in scored if _source_key(i) == src]
        taken = 0
        for item in candidates:
            if taken >= min_n:
                break
            if item.url not in selected_urls:
                selected.append(item)
                selected_urls.add(item.url)
                source_counts[src] += 1
                taken += 1

    # --- Step 5: Fill remaining slots by global score, respecting MAX_PER_SOURCE ---
    for item in scored:
        if len(selected) >= top_n:
            break
        if item.url in selected_urls:
            continue
        src = _source_key(item)
        if source_counts[src] >= MAX_PER_SOURCE:
            continue
        selected.append(item)
        selected_urls.add(item.url)
        source_counts[src] += 1

    # Re-sort final selection by score so the LLM sees best-first
    selected.sort(key=_score, reverse=True)

    logger.info(
        "RankingEngine: %d raw → %d unique → %d selected | per-source: %s",
        len(items), len(unique), len(selected),
        dict(source_counts),
    )
    return selected
