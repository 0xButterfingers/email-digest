"""Tests for config settings."""

import os


def test_archive_base_url_default():
    """ARCHIVE_BASE_URL defaults to archive.0xbutterfingers.xyz."""
    from core.config import Settings

    s = Settings(
        GMAIL_CLIENT_ID="test",
        GMAIL_CLIENT_SECRET="test",
        ANTHROPIC_API_KEY="test",
    )
    assert s.ARCHIVE_BASE_URL == "https://archive.0xbutterfingers.xyz"


def test_archive_base_url_from_env():
    """ARCHIVE_BASE_URL can be overridden via env var."""
    os.environ["ARCHIVE_BASE_URL"] = "https://custom-archive.example.com"
    try:
        from core.config import Settings

        s = Settings(
            GMAIL_CLIENT_ID="test",
            GMAIL_CLIENT_SECRET="test",
            ANTHROPIC_API_KEY="test",
        )
        assert s.ARCHIVE_BASE_URL == "https://custom-archive.example.com"
    finally:
        del os.environ["ARCHIVE_BASE_URL"]
