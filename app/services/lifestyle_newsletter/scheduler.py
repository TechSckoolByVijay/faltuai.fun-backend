"""
APScheduler setup for the Lifestyle Newsletter weekly generation.

The scheduler creates a new ln_podcast_episodes row (status='pending'),
then runs the full worker pipeline.

APScheduler runs in-process (no external queue needed for MVP).
"""
from __future__ import annotations

import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler | None = None


async def _scheduled_generate() -> None:
    """Job invoked by the scheduler — creates an episode and runs the pipeline."""
    logger.info("Scheduler: triggering weekly podcast generation")
    try:
        from app.core.database import AsyncSessionLocal
        from app.services.database.lifestyle_newsletter_service import LnDbService
        from app.services.lifestyle_newsletter.worker import run_pipeline_for_episode

        async with AsyncSessionLocal() as db:
            # Use first active subscriber's key to generate audio (MVP: global episode)
            subscriber = await LnDbService.get_any_active_subscriber_with_key(db)
            encrypted_key = subscriber.elevenlabs_api_key_encrypted if subscriber else None

            episode = await LnDbService.create_episode(db)
            await run_pipeline_for_episode(
                db=db,
                episode_id=episode.id,
                elevenlabs_key_encrypted=encrypted_key,
            )
    except Exception as exc:
        logger.error("Scheduler: scheduled generation failed: %s", exc, exc_info=True)


def start_scheduler() -> None:
    """Start the APScheduler background scheduler. Call once at app startup."""
    global _scheduler

    if not settings.LN_SCHEDULER_ENABLED:
        logger.info("Scheduler: LN_SCHEDULER_ENABLED=False — skipping scheduler start")
        return

    _scheduler = AsyncIOScheduler()

    # Day mapping for CronTrigger
    day_map = {
        "monday": "mon", "tuesday": "tue", "wednesday": "wed",
        "thursday": "thu", "friday": "fri", "saturday": "sat", "sunday": "sun",
    }
    day = day_map.get(settings.LN_WEEKLY_GENERATE_DAY.lower(), "mon")

    _scheduler.add_job(
        _scheduled_generate,
        trigger=CronTrigger(day_of_week=day, hour=6, minute=0),  # 06:00 UTC every week
        id="ln_weekly_generate",
        replace_existing=True,
        misfire_grace_time=3600,  # fire up to 1h late if server was down
    )

    _scheduler.start()
    logger.info("Scheduler: started — weekly generation every %s at 06:00 UTC", day)


def stop_scheduler() -> None:
    """Stop the scheduler on app shutdown."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Scheduler: stopped")
