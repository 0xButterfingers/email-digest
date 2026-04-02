"""Database configuration and session management."""

import logging
from typing import AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from core.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=NullPool,  # Recommended for SQLite with aiosqlite
)

# Create async session factory
async_session_maker = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


async def _migrate_db() -> None:
    """Run lightweight ALTER TABLE migrations for columns added after initial schema."""
    migrations = [
        "ALTER TABLE digest_configs ADD COLUMN scan_hours INTEGER NOT NULL DEFAULT 48",
        "ALTER TABLE digest_configs ADD COLUMN schedule_days VARCHAR(50) NOT NULL DEFAULT 'mon,tue,wed,thu,fri'",
    ]
    async with engine.begin() as conn:
        for sql in migrations:
            try:
                await conn.execute(text(sql))
            except Exception:
                pass  # Column already exists — ignore


async def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import models to register them with Base metadata
        from models.models import Base

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        await _migrate_db()
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        raise


async def close_db() -> None:
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")
        raise
