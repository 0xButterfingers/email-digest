"""Tests for GmailService fetch_emails changes."""

from unittest.mock import MagicMock, patch
from services.gmail_service import GmailService


def _make_mock_message(msg_id, subject="Test", sender="test@test.com", date="2026-04-10"):
    """Create a mock Gmail API message response."""
    return {
        "id": msg_id,
        "payload": {
            "mimeType": "text/plain",
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
                {"name": "Date", "value": date},
            ],
            "body": {
                "data": "SGVsbG8gd29ybGQ=",  # base64("Hello world")
            },
            "parts": [],
        },
    }


def test_fetch_emails_returns_tuple_with_raw_payloads():
    """fetch_emails returns (emails, raw_payloads) tuple."""
    svc = GmailService.__new__(GmailService)

    mock_service = MagicMock()
    mock_service.users().messages().list().execute.return_value = {
        "messages": [{"id": "msg_001"}, {"id": "msg_002"}]
    }
    msg1 = _make_mock_message("msg_001", subject="Alpha")
    msg2 = _make_mock_message("msg_002", subject="Beta")
    mock_service.users().messages().get().execute.side_effect = [msg1, msg2]

    result = svc.fetch_emails(mock_service, "test query", max_results=10, extract_images=False)

    assert isinstance(result, tuple), "fetch_emails must return a tuple"
    assert len(result) == 2, "tuple must have (emails, raw_payloads)"

    emails, raw_payloads = result
    assert len(emails) == 2
    assert isinstance(raw_payloads, dict)
    assert "msg_001" in raw_payloads
    assert "msg_002" in raw_payloads
    assert raw_payloads["msg_001"]["mimeType"] == "text/plain"


def test_parse_email_includes_gmail_message_id():
    """_parse_email includes gmail_message_id field in returned dict."""
    svc = GmailService.__new__(GmailService)
    msg = _make_mock_message("msg_abc123")

    result = svc._parse_email(msg, service=None)

    assert result["gmail_message_id"] == "msg_abc123"
    assert result["id"] == "msg_abc123"
