"""Routes for channel configuration management."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.models import ChannelConfig, DigestConfig
from schemas.schemas import (
    ChannelConfigCreate,
    ChannelConfigUpdate,
    ChannelConfigResponse,
)
from services.channel_service import ChannelService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests/{digest_id}/channels", tags=["channels"])
channel_service = ChannelService()


@router.get("/", response_model=List[ChannelConfigResponse])
async def list_channels(
    digest_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[ChannelConfigResponse]:
    """
    List all channels for a digest.

    Args:
        digest_id: Digest ID
        skip: Number of records to skip
        limit: Maximum records to return
        session: Database session

    Returns:
        List of channel configurations
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Get channels
        stmt = (
            select(ChannelConfig)
            .where(ChannelConfig.digest_id == digest_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        channels = result.scalars().all()
        return channels

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing channels: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve channels",
        )


@router.post("/", response_model=ChannelConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(
    digest_id: int,
    channel: ChannelConfigCreate,
    session: AsyncSession = Depends(get_db),
) -> ChannelConfigResponse:
    """
    Create a new channel configuration.

    Args:
        digest_id: Digest ID
        channel: Channel configuration data
        session: Database session

    Returns:
        Created channel configuration
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Validate channel config
        is_valid, error_msg = channel_service.validate_channel_config(
            channel.channel_type, channel.config or {}
        )
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
            )

        # Create channel
        db_channel = ChannelConfig(
            digest_id=digest_id,
            channel_type=channel.channel_type,
            config=channel.config,
            is_primary=channel.is_primary,
        )
        session.add(db_channel)
        await session.commit()
        logger.info(f"Created channel {db_channel.id} for digest {digest_id}")
        return db_channel

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating channel: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create channel",
        )


@router.put("/{channel_id}", response_model=ChannelConfigResponse)
async def update_channel(
    digest_id: int,
    channel_id: int,
    channel_update: ChannelConfigUpdate,
    session: AsyncSession = Depends(get_db),
) -> ChannelConfigResponse:
    """
    Update a channel configuration.

    Args:
        digest_id: Digest ID
        channel_id: Channel ID
        channel_update: Updated channel data
        session: Database session

    Returns:
        Updated channel configuration
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Get channel
        stmt = select(ChannelConfig).where(
            (ChannelConfig.id == channel_id)
            & (ChannelConfig.digest_id == digest_id)
        )
        result = await session.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
            )

        # Update fields
        if channel_update.channel_type:
            channel.channel_type = channel_update.channel_type
        if channel_update.config is not None:
            channel.config = channel_update.config
        if channel_update.is_primary is not None:
            channel.is_primary = channel_update.is_primary

        # Validate if config changed
        if channel_update.config is not None:
            is_valid, error_msg = channel_service.validate_channel_config(
                channel.channel_type, channel.config
            )
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail=error_msg
                )

        await session.commit()
        logger.info(f"Updated channel {channel_id}")
        return channel

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating channel {channel_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update channel",
        )


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    digest_id: int, channel_id: int, session: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a channel configuration.

    Args:
        digest_id: Digest ID
        channel_id: Channel ID
        session: Database session
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Get and delete channel
        stmt = select(ChannelConfig).where(
            (ChannelConfig.id == channel_id)
            & (ChannelConfig.digest_id == digest_id)
        )
        result = await session.execute(stmt)
        channel = result.scalar_one_or_none()

        if not channel:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found"
            )

        await session.delete(channel)
        await session.commit()
        logger.info(f"Deleted channel {channel_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting channel {channel_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete channel",
        )
