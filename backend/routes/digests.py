"""Routes for digest configuration management."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from core.database import get_db
from models.models import DigestConfig, FilterRule, ChannelConfig
from schemas.schemas import (
    DigestConfigCreate,
    DigestConfigUpdate,
    DigestConfigResponse,
    DigestConfigDetailResponse,
    DigestRunHistoryItem,
    DigestRunResponse,
)
from services.digest_service import DigestService
import routes.scheduler as scheduler_route

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests", tags=["digests"])


@router.get("/", response_model=List[DigestConfigResponse])
async def list_digests(
    skip: int = 0, limit: int = 100, session: AsyncSession = Depends(get_db)
) -> List[DigestConfigResponse]:
    """
    List all digest configurations.

    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        session: Database session

    Returns:
        List of digest configurations
    """
    try:
        stmt = (
            select(DigestConfig)
            .options(selectinload(DigestConfig.filter_rules), selectinload(DigestConfig.channel_configs))
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        digests = result.scalars().all()
        return digests
    except Exception as e:
        logger.error(f"Error listing digests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve digests",
        )


@router.get("/{digest_id}", response_model=DigestConfigDetailResponse)
async def get_digest(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> DigestConfigDetailResponse:
    """
    Get a specific digest configuration with filters and channels.

    Args:
        digest_id: Digest ID
        session: Database session

    Returns:
        Digest configuration with details
    """
    try:
        stmt = (
            select(DigestConfig)
            .options(selectinload(DigestConfig.filter_rules), selectinload(DigestConfig.channel_configs))
            .where(DigestConfig.id == digest_id)
        )
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        return digest
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting digest {digest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve digest",
        )


@router.post("/", response_model=DigestConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_digest(
    digest: DigestConfigCreate,
    session: AsyncSession = Depends(get_db),
) -> DigestConfigResponse:
    """
    Create a new digest configuration.

    Args:
        digest: Digest configuration data
        session: Database session

    Returns:
        Created digest configuration
    """
    try:
        # Check if name already exists
        stmt = select(DigestConfig).where(DigestConfig.name == digest.name)
        result = await session.execute(stmt)
        if result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Digest name already exists",
            )

        # Create digest
        db_digest = DigestConfig(
            name=digest.name,
            schedule_time=digest.schedule_time,
            schedule_days=digest.schedule_days,
            scan_hours=digest.scan_hours,
            is_active=digest.is_active,
            user_id="default",  # Will be set during Gmail auth
        )
        session.add(db_digest)
        await session.flush()

        # Add filter rules
        if digest.filter_rules:
            for filter_rule in digest.filter_rules:
                db_rule = FilterRule(
                    digest_id=db_digest.id,
                    filter_type=filter_rule.filter_type,
                    value=filter_rule.value,
                )
                session.add(db_rule)

        # Add channel configs
        if digest.channel_configs:
            for channel in digest.channel_configs:
                db_channel = ChannelConfig(
                    digest_id=db_digest.id,
                    channel_type=channel.channel_type,
                    config=channel.config,
                    is_primary=channel.is_primary,
                )
                session.add(db_channel)

        await session.commit()
        logger.info(f"Created digest {db_digest.id}: {digest.name}")
        stmt = (
            select(DigestConfig)
            .options(selectinload(DigestConfig.filter_rules), selectinload(DigestConfig.channel_configs))
            .where(DigestConfig.id == db_digest.id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating digest: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create digest",
        )


@router.put("/{digest_id}", response_model=DigestConfigResponse)
async def update_digest(
    digest_id: int,
    digest_update: DigestConfigUpdate,
    session: AsyncSession = Depends(get_db),
) -> DigestConfigResponse:
    """
    Update a digest configuration.

    Args:
        digest_id: Digest ID
        digest_update: Updated digest data
        session: Database session

    Returns:
        Updated digest configuration
    """
    try:
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Check name uniqueness if changing
        if digest_update.name and digest_update.name != digest.name:
            stmt = select(DigestConfig).where(
                DigestConfig.name == digest_update.name
            )
            result = await session.execute(stmt)
            if result.scalar_one_or_none():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Digest name already exists",
                )

        # Track whether schedule changed so we can re-sync the cron job
        schedule_changed = False

        # Update fields
        if digest_update.name:
            digest.name = digest_update.name
        if digest_update.schedule_time:
            if digest_update.schedule_time != digest.schedule_time:
                schedule_changed = True
            digest.schedule_time = digest_update.schedule_time
        if digest_update.schedule_days is not None:
            if digest_update.schedule_days != digest.schedule_days:
                schedule_changed = True
            digest.schedule_days = digest_update.schedule_days
        if digest_update.scan_hours is not None:
            digest.scan_hours = digest_update.scan_hours
        if digest_update.is_active is not None:
            if digest_update.is_active != digest.is_active:
                schedule_changed = True
            digest.is_active = digest_update.is_active

        await session.commit()
        logger.info(f"Updated digest {digest_id}")

        # Re-sync scheduler if anything schedule-related changed
        if schedule_changed and scheduler_route.scheduler_service:
            if digest.is_active:
                await scheduler_route.scheduler_service.schedule_digest(
                    digest_id, digest.schedule_time, digest.schedule_days
                )
            else:
                await scheduler_route.scheduler_service.unschedule_digest(digest_id)

        stmt = (
            select(DigestConfig)
            .options(selectinload(DigestConfig.filter_rules), selectinload(DigestConfig.channel_configs))
            .where(DigestConfig.id == digest_id)
        )
        result = await session.execute(stmt)
        return result.scalar_one()

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating digest {digest_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update digest",
        )


@router.delete("/{digest_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_digest(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a digest configuration.

    Args:
        digest_id: Digest ID
        session: Database session
    """
    try:
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        await session.delete(digest)
        await session.commit()
        logger.info(f"Deleted digest {digest_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting digest {digest_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete digest",
        )


@router.post("/{digest_id}/run/", response_model=DigestRunResponse)
async def run_digest(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> DigestRunResponse:
    """
    Manually trigger a digest run.

    Args:
        digest_id: Digest ID
        session: Database session

    Returns:
        Run result
    """
    try:
        # Verify the digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()
        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        service = DigestService()
        history = await service.run_digest(digest_id, session)

        if history is None:
            return DigestRunResponse(
                success=False,
                message="Digest run failed or digest is inactive",
            )

        return DigestRunResponse(
            success=history.status.value == "success",
            message=f"Digest run completed with status: {history.status.value}",
            history_id=history.id,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error running digest {digest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to run digest",
        )


@router.get("/{digest_id}/history/", response_model=List[DigestRunHistoryItem])
async def get_digest_history(
    digest_id: int, limit: int = 20, session: AsyncSession = Depends(get_db)
) -> List[DigestRunHistoryItem]:
    """
    Get execution history for a digest.

    Args:
        digest_id: Digest ID
        limit: Maximum number of records to return
        session: Database session

    Returns:
        List of history records
    """
    try:
        # Verify the digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        service = DigestService()
        records = await service.get_digest_history(digest_id, limit=limit, session=session)

        return [
            DigestRunHistoryItem(
                id=r.id,
                status=r.status,
                timestamp=r.sent_at or r.created_at,
                duration=None,
                emails_processed=r.email_count or 0,
                emails_sent=r.email_count or 0,
                error=r.error_message,
                summary=r.summary,
                channels_count=1 if r.channel_used else 0,
            )
            for r in records
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching history for digest {digest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve digest history",
        )
