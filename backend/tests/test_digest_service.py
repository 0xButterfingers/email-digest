"""Tests for DigestService orchestration wiring."""

from unittest.mock import patch
from services.digest_service import DigestService


def test_digest_service_imports_archive_service():
    with patch("services.email_archive_service.ARCHIVE_DIR") as mock_dir:
        mock_dir.mkdir.return_value = None
        svc = DigestService.__new__(DigestService)
        svc.__init__()
    assert hasattr(svc, "archive_service")


def test_digest_service_has_all_services():
    with patch("services.email_archive_service.ARCHIVE_DIR") as mock_dir:
        mock_dir.mkdir.return_value = None
        svc = DigestService()
    assert hasattr(svc, "gmail_service")
    assert hasattr(svc, "llm_service")
    assert hasattr(svc, "channel_service")
    assert hasattr(svc, "pdf_service")
    assert hasattr(svc, "archive_service")
