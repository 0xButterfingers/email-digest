"""FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.config import settings
from core.database import init_db, close_db
from routes import (
    digests_router,
    filters_router,
    channels_router,
    gmail_router,
    scheduler_router,
)
from routes.scheduler import set_scheduler
from services.scheduler_service import SchedulerService

logger = logging.getLogger(__name__)

# Initialize scheduler service (global)
scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for app startup and shutdown.

    Args:
        app: FastAPI application instance
    """
    # Startup
    try:
        logger.info("Starting up application")

        # Initialize database
        await init_db()
        logger.info("Database initialized")

        # Initialize scheduler
        await scheduler_service.init_scheduler()
        logger.info("Scheduler initialized")

        # Set scheduler in routes
        set_scheduler(scheduler_service)

        yield

    except Exception as e:
        logger.error(f"Error during startup: {e}")
        raise

    finally:
        # Shutdown
        try:
            logger.info("Shutting down application")

            # Shutdown scheduler
            await scheduler_service.shutdown_scheduler()
            logger.info("Scheduler shutdown complete")

            # Close database
            await close_db()
            logger.info("Database closed")

        except Exception as e:
            logger.error(f"Error during shutdown: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Email Digest Summarizer Backend API",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include routers
app.include_router(digests_router)
app.include_router(filters_router)
app.include_router(channels_router)
app.include_router(gmail_router)
app.include_router(scheduler_router)


# Health check endpoint
@app.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint.

    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root() -> dict:
    """
    Root endpoint with API information.

    Returns:
        API information
    """
    return {
        "message": "Email Digest Summarizer API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "openapi": "/openapi.json",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )
