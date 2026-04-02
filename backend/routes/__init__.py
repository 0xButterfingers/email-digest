"""Routes package."""

from routes.digests import router as digests_router
from routes.filters import router as filters_router
from routes.channels import router as channels_router
from routes.gmail import router as gmail_router
from routes.scheduler import router as scheduler_router

__all__ = [
    "digests_router",
    "filters_router",
    "channels_router",
    "gmail_router",
    "scheduler_router",
]
