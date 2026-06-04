"""
Worker — orchestrates the full AI Audio Newsletter pipeline.

Pipeline steps:
  1. Fetch data from all enabled adapters (GitHub, HackerNews, Reddit, ArXiv, Articles)
  2. Apply user topic + source preferences
  3. Rank and filter content
  4. Run LangGraph LLM pipeline → newsletter markdown
  5. Generate audio via ElevenLabs (BYOK: uses subscriber's decrypted key)
  6. Save results → update ln_podcast_episodes row
  7. Mark episode as 'ready'
"""
from __future__ import annotations

import logging
from typing import Dict, Any, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.services.lifestyle_newsletter.adapters.github_adapter import GitHubAdapter
from app.services.lifestyle_newsletter.adapters.hackernews_adapter import HackerNewsAdapter
from app.services.lifestyle_newsletter.adapters.reddit_adapter import RedditAdapter
from app.services.lifestyle_newsletter.adapters.arxiv_adapter import ArXivAdapter
from app.services.lifestyle_newsletter.adapters.articles_adapter import ArticlesAdapter
from app.services.lifestyle_newsletter.adapters.producthunt_adapter import ProductHuntAdapter
from app.services.lifestyle_newsletter.adapters.topic_search_adapter import fetch_topic_news
from app.services.lifestyle_newsletter import ranking_engine
from app.services.lifestyle_newsletter.llm_pipeline import run_pipeline
from app.services.lifestyle_newsletter import audio_service
from app.services.lifestyle_newsletter import progress_store as ps
from app.services.lifestyle_newsletter.user_key_service import decrypt_elevenlabs_key, decrypt_key
from app.services.database.lifestyle_newsletter_service import LnDbService
from app.schemas.lifestyle_newsletter import NormalizedContent

logger = logging.getLogger(__name__)

# Map source names → adapter classes
ALL_ADAPTERS = {
    "github": GitHubAdapter,
    "hackernews": HackerNewsAdapter,
    "reddit": RedditAdapter,
    "arxiv": ArXivAdapter,
    "articles": ArticlesAdapter,
    "producthunt": ProductHuntAdapter,
}

SOURCE_LABELS = {
    "github":        "🐙 GitHub",
    "hackernews":    "🟠 Hacker News",
    "reddit":        "🔴 Reddit",
    "arxiv":         "📄 ArXiv",
    "articles":      "📰 Blogs",
    "producthunt":   "🛠️ Product Hunt",
    "topic_search":  "🎯 Topic Search",
}


def _fallback_script(top_items: List[NormalizedContent], presentation_mode: str = "news") -> str:
    """Build a deterministic script when the LLM step is unavailable (e.g., quota/rate errors)."""
    top_items = top_items[:8]
    if presentation_mode == "podcast":
        lines = [
            "Speaker A: Welcome to Faltu AI Weekly. OpenAI was unavailable right now, so this is a quick fallback briefing with the top stories.",
            "Speaker B: Here are the most important updates from this run.",
        ]
        for idx, item in enumerate(top_items, 1):
            summary = (item.summary or "No summary available.").replace("\n", " ").strip()
            summary = summary[:280]
            lines.append(f"Speaker A: Story {idx} is {item.title}.")
            lines.append(f"Speaker B: {summary} Source: {item.source}. Link: {item.url or 'N/A'}")
        lines.append("Speaker A: That is the fallback edition. We will return to full AI-written analysis on the next run.")
        return "\n".join(lines)

    lines = [
        "## Introduction",
        "This is a fallback edition generated without the LLM because the AI provider was temporarily unavailable.",
        "",
        "## Top Stories",
    ]
    for idx, item in enumerate(top_items, 1):
        summary = (item.summary or "No summary available.").replace("\n", " ").strip()
        lines.append(f"### {idx}. {item.title}")
        lines.append(summary[:420])
        lines.append(f"- Source: {item.source}")
        lines.append(f"- Link: {item.url or 'N/A'}")
        lines.append("")

    lines.extend([
        "## The Faltu Take",
        "This fallback newsletter keeps your feed moving even when the LLM is unavailable. Re-run generation later for the full editorial version.",
    ])
    return "\n".join(lines)
DEFAULT_SOURCES = list(ALL_ADAPTERS.keys())


def _apply_topic_filters(
    items: List[NormalizedContent],
    topics_follow: Optional[List[str]],
    topics_exclude: Optional[List[str]],
) -> List[NormalizedContent]:
    """
    Filter items by user topic preferences.
    - If topics_follow is set, boost items matching those topics (move to front)
      but keep everything (don't remove non-matching items).
    - If topics_exclude is set, remove items whose title/summary contain excluded terms.
    """
    if topics_exclude:
        excl_lower = [t.lower() for t in topics_exclude]
        items = [
            it for it in items
            if not any(
                excl in it.title.lower() or excl in it.summary.lower()
                for excl in excl_lower
            )
        ]

    if topics_follow:
        follow_lower = [t.lower() for t in topics_follow]
        def _matches(it: NormalizedContent) -> bool:
            combined = (it.title + " " + it.summary).lower()
            return any(f in combined for f in follow_lower)
        preferred = [it for it in items if _matches(it)]
        others = [it for it in items if not _matches(it)]
        items = preferred + others

    return items


async def run_pipeline_for_episode(
    db: AsyncSession,
    episode_id: int,
    elevenlabs_key_encrypted: Optional[str] = None,
    user_prefs: Optional[Dict[str, Any]] = None,
    generate_audio: bool = True,
) -> None:
    """
    Full pipeline execution for a given episode_id.
    On success:  episode.status = 'ready', audio_url + script + sources_metadata saved.
    On failure:  episode.status = 'failed', episode.error_message set.
    """
    try:
        await LnDbService.update_episode_status(db, episode_id, "generating")
        ps.add(episode_id, "Starting newsletter generation…", "step")

        prefs = user_prefs or {}
        sources_enabled: List[str] = prefs.get("sources_enabled") or DEFAULT_SOURCES
        topics_follow: Optional[List[str]] = prefs.get("topics_follow")
        topics_exclude: Optional[List[str]] = prefs.get("topics_exclude")
        custom_topics: Optional[List[str]] = prefs.get("custom_topics")
        priority_people: Optional[List[str]] = prefs.get("priority_people")
        presentation_mode: str = prefs.get("presentation_mode") or "news"
        audio_provider: str = prefs.get("audio_provider") or "elevenlabs"
        deepgram_key_encrypted: Optional[str] = prefs.get("deepgram_key_encrypted")
        voice_id: Optional[str] = prefs.get("voice_id")
        fallback_enabled: bool = prefs.get("fallback_enabled", True)

        # Override lookback window for this run if the user specified one
        _original_lookback = settings.LN_CONTENT_LOOKBACK_DAYS
        if prefs.get("lookback_days"):
            settings.LN_CONTENT_LOOKBACK_DAYS = int(prefs["lookback_days"])
            logger.info("Worker: lookback_days overridden to %d for episode %d", settings.LN_CONTENT_LOOKBACK_DAYS, episode_id)

        lookback = settings.LN_CONTENT_LOOKBACK_DAYS
        ps.add(episode_id, f"🔍 Fetching stories from {len(sources_enabled)} sources (last {lookback}d)…", "info")

        # Step 0: Active topic search via Google (Serper) — runs FIRST when focus topics or priority people are set
        all_items: List[NormalizedContent] = []
        # Build combined search queries: topics_follow + priority_people (each person searched as "<name> AI")
        search_queries: List[str] = list(topics_follow or [])
        for person in (priority_people or []):
            search_queries.append(f"{person} AI")
        if search_queries and settings.SERPER_API_KEY:
            ps.add(episode_id, f"🔎 Searching the web for: {', '.join(search_queries)}…", "step")
            topic_items = await fetch_topic_news(search_queries, lookback_days=settings.LN_CONTENT_LOOKBACK_DAYS)
            if topic_items:
                ps.add(episode_id, f"🎯 Topic search found {len(topic_items)} relevant articles", "success")
                all_items.extend(topic_items)
            else:
                ps.add(episode_id, "ℹ️ Topic search returned no results — continuing with regular sources", "info")
        elif search_queries:
            ps.add(episode_id, "ℹ️ SERPER_API_KEY not set — skipping web topic search", "info")
        for source_name in sources_enabled:
            adapter_cls = ALL_ADAPTERS.get(source_name)
            if not adapter_cls:
                logger.warning("Worker: unknown source '%s', skipping", source_name)
                continue
            adapter = adapter_cls()
            try:
                items = await adapter.fetch()
                label = SOURCE_LABELS.get(source_name, source_name)
                ps.add(episode_id, f"{label}: {len(items)} items", "info")
                logger.info("Adapter %s fetched %d items", source_name, len(items))
                for it in items:
                    logger.info("  [%s] %s | content_len=%d", it.source, it.title[:60], len(it.summary))
                all_items.extend(items)
            except Exception as exc:
                ps.add(episode_id, f"⚠️ {SOURCE_LABELS.get(source_name, source_name)} failed: {exc}", "error")
                logger.warning("Adapter %s failed: %s", source_name, exc)

        logger.info("Worker: fetched %d total items across all adapters", len(all_items))
        ps.add(episode_id, f"📦 {len(all_items)} total items collected across all sources", "info")

        # Restore the global lookback setting so future/concurrent runs are not affected
        settings.LN_CONTENT_LOOKBACK_DAYS = _original_lookback

        # Step 2b: Apply user topic filters (also boost priority_people mentions)
        effective_follow = list(topics_follow or []) + list(priority_people or [])
        if effective_follow or topics_exclude:
            before = len(all_items)
            all_items = _apply_topic_filters(all_items, effective_follow or None, topics_exclude)
            ps.add(episode_id, f"🎯 Topic filter: {before} → {len(all_items)} items", "info")
            logger.info(
                "Worker: topic filter reduced %d → %d items (follow=%s, exclude=%s)",
                before, len(all_items), topics_follow, topics_exclude,
            )

        # Step 3: Rank
        ps.add(episode_id, "⚖️ Ranking and selecting top stories…", "step")
        top_items = ranking_engine.rank(all_items)
        if not top_items:
            raise ValueError("Ranking engine returned no items — nothing to generate.")
        ps.add(episode_id, f"✅ Selected {len(top_items)} top stories", "info")

        # Step 4: LLM pipeline → newsletter markdown
        ps.add(episode_id, "✍️ Writing newsletter with AI (this takes ~30s)…", "step")
        try:
            script = await run_pipeline(
                top_items,
                topics_follow=topics_follow,
                topics_exclude=topics_exclude,
                custom_topics=custom_topics,
                priority_people=priority_people,
                presentation_mode=presentation_mode,
            )
            ps.add(episode_id, "📝 Newsletter script ready", "info")
        except Exception as exc:
            logger.warning("Worker: LLM pipeline failed, using fallback script: %s", exc)
            ps.add(episode_id, "⚠️ AI writer unavailable — using fallback script", "error")
            script = _fallback_script(top_items, presentation_mode=presentation_mode)
            ps.add(episode_id, "📝 Fallback newsletter script ready", "info")

        # Build a concise episode title from the top story
        # Sanitize: fall back to generic title if top story looks off-topic
        _candidate_title = top_items[0].title[:60] if top_items else ""
        _blocked_in_title = any(
            term in _candidate_title.lower()
            for term in ["jailbreak", "nsfw", "porn", "sex", "nude", "bypass", "meme"]
        )
        title = (
            f"Faltu AI Weekly — {_candidate_title}"
            if top_items and not _blocked_in_title
            else "Faltu AI Weekly"
        )
        sources_meta = [item.model_dump() for item in top_items]

        # Step 5: Audio generation (only if enabled and user has at least one BYOK key)
        audio_url: Optional[str] = None
        has_any_key = bool(elevenlabs_key_encrypted or deepgram_key_encrypted)
        if generate_audio and has_any_key:
            provider_label = audio_provider.capitalize()
            ps.add(episode_id, f"🔊 Generating audio ({provider_label}, {presentation_mode} mode)…", "step")
            try:
                raw_el_key = decrypt_elevenlabs_key(elevenlabs_key_encrypted) if elevenlabs_key_encrypted else None
                raw_dg_key = decrypt_key(deepgram_key_encrypted) if deepgram_key_encrypted else None
                audio_bytes = await audio_service.generate_audio_with_fallback(
                    script=script,
                    presentation_mode=presentation_mode,
                    elevenlabs_key=raw_el_key,
                    deepgram_key=raw_dg_key,
                    voice_id=voice_id,  # None is fine — audio_service picks the right default per provider
                    audio_provider=audio_provider,
                    fallback_enabled=fallback_enabled,
                )
                del raw_el_key, raw_dg_key
                if audio_bytes:
                    audio_url = await audio_service.save_audio_to_storage(audio_bytes, episode_id)
                    ps.add(episode_id, "🎧 Audio ready!", "info")
                else:
                    ps.add(episode_id, "⚠️ Audio generation returned empty — newsletter still available", "error")
            except Exception as exc:
                ps.add(episode_id, f"⚠️ Audio failed (newsletter still available): {exc}", "error")
                logger.warning("Worker: audio generation failed (continuing without audio): %s", exc)
        elif not generate_audio:
            ps.add(episode_id, "ℹ️ Content-only mode: audio generation skipped", "info")
        else:
            ps.add(episode_id, "ℹ️ No audio provider key saved — skipping audio", "info")

        # Step 6 & 7: Save + mark ready
        ps.add(episode_id, "💾 Saving episode…", "step")
        await LnDbService.complete_episode(
            db=db,
            episode_id=episode_id,
            title=title,
            script=script,
            audio_url=audio_url,
            sources_metadata=sources_meta,
        )
        ps.add(episode_id, "🎉 Episode ready! Refresh to read.", "success")
        logger.info("Worker: episode %d completed (audio=%s)", episode_id, bool(audio_url))

    except Exception as exc:
        ps.add(episode_id, f"💥 Generation failed: {exc}", "error")
        logger.error("Worker: pipeline failed for episode %d: %s", episode_id, exc, exc_info=True)
        await LnDbService.fail_episode(db, episode_id, str(exc))
