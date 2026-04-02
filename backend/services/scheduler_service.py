"""Service for scheduling digest execution."""

import logging
from datetime import time, datetime
from typing import List, Optional, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from core.config import settings
from core.database import async_session_maker
from models.models import DigestConfig
from services.digest_service import DigestService
from sqlalchemy import select

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing digest scheduling."""

    def __init__(self):
        """Initialize scheduler service."""
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.digest_service = DigestService()
        self.digest_callbacks: List[Callable] = []

    async def init_scheduler(self) -> None:
        """Initialize and configure the scheduler."""
        try:
            if self.scheduler is None:
                self.scheduler = AsyncIOScheduler(timezone=settings.SCHEDULER_TIMEZONE)
                self.scheduler.start()
                logger.info("Scheduler initialized")

            # Load and schedule all active digests
            await self._sync_jobs()
            logger.info("Scheduler jobs synced with database")

        except Exception as e:
            logger.error(f"Error initializing scheduler: {e}")
            raise

    async def shutdown_scheduler(self) -> None:
        """Shutdown the scheduler."""
        try:
            if self.scheduler:
                self.scheduler.shutdown(wait=True)
                logger.info("Scheduler shutdown complete")
        except Exception as e:
            logger.error(f"Error shutting down scheduler: {e}")

    async def _sync_jobs(self) -> None:
        """Sync scheduler jobs with database digests."""
        try:
            async with async_session_maker() as session:
                stmt = select(DigestConfig).where(DigestConfig.is_active == True)
                result = await session.execute(stmt)
                digests = result.scalars().all()

            # Remove all existing jobs
            if self.scheduler:
                self.scheduler.remove_all_jobs()

            # Schedule active digests
            for digest in digests:
                await self.schedule_digest(
                    digest.id,
                    digest.schedule_time,
                    getattr(digest, "schedule_days", None) or "mon,tue,wed,thu,fri",
                )

            logger.info(f"Synced {len(digests)} digest jobs")

        except Exception as e:
            logger.error(f"Error syncing jobs: {e}")

    async def schedule_digest(
        self,
        digest_id: int,
        schedule_time: str,
        schedule_days: str = "mon,tue,wed,thu,fri",
    ) -> bool:
        """
        Schedule a digest to run at specified time and days.

        Args:
            digest_id: Digest configuration ID
            schedule_time: Schedule time in "HH:MM" format
            schedule_days: Comma-separated day abbreviations (mon,tue,wed,thu,fri,sat,sun)

        Returns:
            Success status
        """
        try:
            if not self.scheduler:
                logger.error("Scheduler not initialized")
                return False

            # Parse time
            try:
                hour, minute = map(int, schedule_time.split(":"))
            except ValueError:
                logger.error(f"Invalid schedule time format: {schedule_time}")
                return False

            day_of_week = schedule_days if schedule_days else "mon,tue,wed,thu,fri"

            # Remove existing job if present
            job_id = f"digest_{digest_id}"
            try:
                self.scheduler.remove_job(job_id)
            except:
                pass

            # Create cron trigger
            trigger = CronTrigger(
                day_of_week=day_of_week,
                hour=hour,
                minute=minute,
                timezone=settings.SCHEDULER_TIMEZONE,
            )

            # Add job
            self.scheduler.add_job(
                self._run_digest_job,
                trigger=trigger,
                id=job_id,
                args=[digest_id],
                misfire_grace_time=600,  # 10 minutes grace period
                replace_existing=True,
            )

            logger.info(f"Scheduled digest {digest_id} at {schedule_time} on {day_of_week}")
            return True

        except Exception as e:
            logger.error(f"Error scheduling digest: {e}")
            return False

    async def unschedule_digest(self, digest_id: int) -> bool:
        """
        Remove digest from scheduler.

        Args:
            digest_id: Digest configuration ID

        Returns:
            Success status
        """
        try:
            if not self.scheduler:
                logger.error("Scheduler not initialized")
                return False

            job_id = f"digest_{digest_id}"
            try:
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed digest {digest_id} from scheduler")
                return True
            except Exception:
                logger.warning(f"Job {job_id} not found in scheduler")
                return True

        except Exception as e:
            logger.error(f"Error unscheduling digest: {e}")
            return False

    async def _run_digest_job(self, digest_id: int) -> None:
        """
        Execute digest job.

        Args:
            digest_id: Digest configuration ID
        """
        try:
            logger.info(f"Running scheduled digest {digest_id}")
            async with async_session_maker() as session:
                history = await self.digest_service.run_digest(digest_id, session)

            # Trigger callbacks
            for callback in self.digest_callbacks:
                try:
                    await callback(digest_id, history)
                except Exception as e:
                    logger.error(f"Error in digest callback: {e}")

        except Exception as e:
            logger.error(f"Error running digest job {digest_id}: {e}")

    async def run_digest_now(self, digest_id: int) -> bool:
        """
        Manually trigger a digest run immediately.

        Args:
            digest_id: Digest configuration ID

        Returns:
            Success status
        """
        try:
            logger.info(f"Manually triggering digest {digest_id}")
            await self._run_digest_job(digest_id)
            return True
        except Exception as e:
            logger.error(f"Error running digest manually: {e}")
            return False

    def get_jobs(self) -> dict:
        """
        Get current scheduler jobs.

        Returns:
            Dictionary of job information
        """
        try:
            if not self.scheduler:
                return {}

            jobs_info = {}
            for job in self.scheduler.get_jobs():
                jobs_info[job.id] = {
                    "id": job.id,
                    "name": job.name,
                    "trigger": str(job.trigger),
                    "next_run_time": job.next_run_time.isoformat()
                    if job.next_run_time
                    else None,
                }

            return jobs_info

        except Exception as e:
            logger.error(f"Error getting jobs: {e}")
            return {}

    def is_running(self) -> bool:
        """
        Check if scheduler is running.

        Returns:
            Running status
        """
        return self.scheduler is not None and self.scheduler.running

    async def register_callback(self, callback: Callable) -> None:
        """
        Register a callback for digest completion.

        Args:
            callback: Async callable(digest_id, history)
        """
        self.digest_callbacks.append(callback)
        logger.info(f"Registered callback {callback.__name__}")

    async def update_digest_schedule(
        self, digest_id: int, new_schedule_time: str
    ) -> bool:
        """
        Update digest schedule time.

        Args:
            digest_id: Digest configuration ID
            new_schedule_time: New schedule time in "HH:MM" format

        Returns:
            Success status
        """
        try:
            # Update in database
            async with async_session_maker() as session:
                stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
                result = await session.execute(stmt)
                digest = result.scalar_one_or_none()

                if not digest:
                    logger.error(f"Digest {digest_id} not found")
                    return False

                digest.schedule_time = new_schedule_time
                await session.commit()

            # Reschedule job
            if digest.is_active:
                await self.schedule_digest(digest_id, new_schedule_time)

            logger.info(f"Updated schedule for digest {digest_id} to {new_schedule_time}")
            return True

        except Exception as e:
            logger.error(f"Error updating digest schedule: {e}")
            return False

    def get_status(self) -> dict:
        """
        Get scheduler status.

        Returns:
            Status information
        """
        try:
            jobs = self.get_jobs()
            return {
                "is_running": self.is_running(),
                "jobs_count": len(jobs),
                "active_digests": len(
                    [job_id for job_id in jobs if job_id.startswith("digest_")]
                ),
                "jobs": jobs,
            }
        except Exception as e:
            logger.error(f"Error getting scheduler status: {e}")
            return {
                "is_running": False,
                "jobs_count": 0,
                "active_digests": 0,
                "error": str(e),
            }
