"""Routes for scheduler management and digest execution."""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import get_db
from schemas.schemas import (
    SchedulerStatus,
    ManualRunRequest,
    ManualRunResponse,
    DigestHistoryResponse,
)
from services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scheduler", tags=["scheduler"])

# Scheduler service instance (will be injected from main.py)
scheduler_service: SchedulerService = None


def set_scheduler(scheduler: SchedulerService) -> None:
    """Set the scheduler service instance."""
    global scheduler_service
    scheduler_service = scheduler


@router.get("/status", response_model=SchedulerStatus)
async def get_scheduler_status() -> SchedulerStatus:
    """
    Get current scheduler status.

    Returns:
        Scheduler status
    """
    try:
        if not scheduler_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler not initialized",
            )

        status_dict = scheduler_service.get_status()
        return SchedulerStatus(
            is_running=status_dict["is_running"],
            jobs_count=status_dict["jobs_count"],
            active_digests=status_dict["active_digests"],
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduler status",
        )


@router.post("/digest/run", response_model=ManualRunResponse)
async def run_digest_now(
    request: ManualRunRequest, session: AsyncSession = Depends(get_db)
) -> ManualRunResponse:
    """
    Manually trigger a digest run.

    Args:
        request: Manual run request
        session: Database session

    Returns:
        Run status
    """
    try:
        if not scheduler_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler not initialized",
            )

        # Run digest
        success = await scheduler_service.run_digest_now(request.digest_id)

        if not success:
            return ManualRunResponse(
                success=False, message="Failed to run digest"
            )

        return ManualRunResponse(
            success=True, message=f"Digest {request.digest_id} triggered successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running digest manually: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run digest",
        )


@router.get("/jobs")
async def get_scheduled_jobs() -> dict:
    """
    Get all scheduled jobs.

    Returns:
        Dictionary of job information
    """
    try:
        if not scheduler_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler not initialized",
            )

        jobs = scheduler_service.get_jobs()
        return {"jobs": jobs, "count": len(jobs)}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting scheduled jobs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get scheduled jobs",
        )


@router.post("/digest/{digest_id}/schedule")
async def schedule_digest(
    digest_id: int,
    schedule_time: str,
    session: AsyncSession = Depends(get_db),
) -> dict:
    """
    Schedule a digest with a specific time.

    Args:
        digest_id: Digest ID
        schedule_time: Schedule time in "HH:MM" format
        session: Database session

    Returns:
        Scheduling status
    """
    try:
        if not scheduler_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler not initialized",
            )

        # Validate time format
        try:
            hour, minute = map(int, schedule_time.split(":"))
            if not (0 <= hour < 24 and 0 <= minute < 60):
                raise ValueError()
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid schedule time format. Use HH:MM",
            )

        success = await scheduler_service.schedule_digest(digest_id, schedule_time)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to schedule digest",
            )

        return {
            "success": True,
            "message": f"Digest {digest_id} scheduled at {schedule_time}",
            "digest_id": digest_id,
            "schedule_time": schedule_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scheduling digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to schedule digest",
        )


@router.post("/digest/{digest_id}/unschedule")
async def unschedule_digest(digest_id: int) -> dict:
    """
    Remove a digest from scheduler.

    Args:
        digest_id: Digest ID

    Returns:
        Unscheduling status
    """
    try:
        if not scheduler_service:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Scheduler not initialized",
            )

        success = await scheduler_service.unschedule_digest(digest_id)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to unschedule digest",
            )

        return {
            "success": True,
            "message": f"Digest {digest_id} removed from scheduler",
            "digest_id": digest_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unscheduling digest: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to unschedule digest",
        )
