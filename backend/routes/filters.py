"""Routes for email filter management."""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.models import FilterRule, DigestConfig
from schemas.schemas import FilterRuleCreate, FilterRuleUpdate, FilterRuleResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digests/{digest_id}/filters", tags=["filters"])


@router.get("/", response_model=List[FilterRuleResponse])
async def list_filters(
    digest_id: int,
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_db),
) -> List[FilterRuleResponse]:
    """
    List all filters for a digest.

    Args:
        digest_id: Digest ID
        skip: Number of records to skip
        limit: Maximum records to return
        session: Database session

    Returns:
        List of filter rules
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Get filters
        stmt = (
            select(FilterRule)
            .where(FilterRule.digest_id == digest_id)
            .offset(skip)
            .limit(limit)
        )
        result = await session.execute(stmt)
        filters = result.scalars().all()
        return filters

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing filters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve filters",
        )


@router.post("/", response_model=FilterRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_filter(
    digest_id: int,
    filter_rule: FilterRuleCreate,
    session: AsyncSession = Depends(get_db),
) -> FilterRuleResponse:
    """
    Create a new filter rule.

    Args:
        digest_id: Digest ID
        filter_rule: Filter rule data
        session: Database session

    Returns:
        Created filter rule
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Create filter
        db_filter = FilterRule(
            digest_id=digest_id,
            filter_type=filter_rule.filter_type,
            value=filter_rule.value,
        )
        session.add(db_filter)
        await session.commit()
        logger.info(f"Created filter {db_filter.id} for digest {digest_id}")
        return db_filter

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating filter: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create filter",
        )


@router.put("/{filter_id}", response_model=FilterRuleResponse)
async def update_filter(
    digest_id: int,
    filter_id: int,
    filter_update: FilterRuleUpdate,
    session: AsyncSession = Depends(get_db),
) -> FilterRuleResponse:
    """
    Update a filter rule.

    Args:
        digest_id: Digest ID
        filter_id: Filter ID
        filter_update: Updated filter data
        session: Database session

    Returns:
        Updated filter rule
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Get filter
        stmt = select(FilterRule).where(
            (FilterRule.id == filter_id) & (FilterRule.digest_id == digest_id)
        )
        result = await session.execute(stmt)
        filter_rule = result.scalar_one_or_none()

        if not filter_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found"
            )

        # Update fields
        if filter_update.filter_type:
            filter_rule.filter_type = filter_update.filter_type
        if filter_update.value:
            filter_rule.value = filter_update.value

        await session.commit()
        logger.info(f"Updated filter {filter_id}")
        return filter_rule

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating filter {filter_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update filter",
        )


@router.delete("/{filter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter(
    digest_id: int, filter_id: int, session: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete a filter rule.

    Args:
        digest_id: Digest ID
        filter_id: Filter ID
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

        # Get and delete filter
        stmt = select(FilterRule).where(
            (FilterRule.id == filter_id) & (FilterRule.digest_id == digest_id)
        )
        result = await session.execute(stmt)
        filter_rule = result.scalar_one_or_none()

        if not filter_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Filter not found"
            )

        await session.delete(filter_rule)
        await session.commit()
        logger.info(f"Deleted filter {filter_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting filter {filter_id}: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete filter",
        )
