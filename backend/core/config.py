"""Configuration module for the email digest application."""

import logging
from pathlib import Path

from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "Email Digest Summarizer"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./email_digest.db"

    # Gmail OAuth2
    GMAIL_CLIENT_ID: str
    GMAIL_CLIENT_SECRET: str
    GMAIL_REDIRECT_URI: str = "http://localhost:8000/auth/gmail/callback"
    GMAIL_SCOPES: list = [
        "https://www.googleapis.com/auth/gmail.readonly",
        "https://www.googleapis.com/auth/gmail.modify",
    ]

    # Claude API
    ANTHROPIC_API_KEY: str

    # Twilio
    TWILIO_ACCOUNT_SID: str = ""
    TWILIO_AUTH_TOKEN: str = ""
    TWILIO_WHATSAPP_FROM: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""

    # Discord
    DISCORD_WEBHOOK_URL: str = ""

    # CORS
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:8000"]

    # Scheduler
    SCHEDULER_TIMEZONE: str = "UTC"
    SCHEDULER_POOL_SIZE: int = 10

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()


settings = get_settings()

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
