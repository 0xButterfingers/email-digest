"""Tests for LLM service structured output."""

from unittest.mock import MagicMock
from services.llm_service import LLMService


MOCK_EXECUTIVE = '<b>📊 Daily Bank Reports — Executive Summary</b>\n\n<b>Macro</b>\n• JPM: US CPI at 2.4% YoY'

MOCK_DETAILED_TEXT = """Macro
## US CPI — March print at 2.4% YoY
Core CPI fell to 2.8% from 3.0%. Markets pricing 3 cuts by year-end.
Source: Email 1

FX
## EUR/USD — Rallied to 1.0920 post-CPI
Dollar weakness broad-based. DXY broke below 104.
Source: Email 2
"""


def _make_mock_response(text):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    return mock_msg


def test_summarize_returns_detailed_items_from_plain_text():
    """When LLM returns plain text with ## headings, detailed_items is a list."""
    svc = LLMService.__new__(LLMService)
    svc.client = MagicMock()
    svc.model = "claude-sonnet-4-6"

    raw_response = f"{MOCK_EXECUTIVE}\n\n---DETAILED---\n\n{MOCK_DETAILED_TEXT}"
    svc.client.messages.create.return_value = _make_mock_response(raw_response)

    result = svc.summarize_emails(
        [{"sender": "a@test.com", "subject": "Test", "date": "2026-04-10", "body": "content"}],
        "Test Digest",
    )

    assert "detailed_items" in result
    assert isinstance(result["detailed_items"], list)
    assert len(result["detailed_items"]) == 2
    assert result["detailed_items"][0]["category"] == "Macro"
    assert result["detailed_items"][0]["source_email_index"] == 0
    assert result["detailed_items"][1]["category"] == "FX"
    assert result["detailed_items"][1]["source_email_index"] == 1
    assert result["executive"] == MOCK_EXECUTIVE


def test_parse_detailed_text_handles_dash_format():
    """Parser handles old-style '- ' item format as fallback."""
    text = """Macro
- US CPI: 2.4% YoY
Core CPI at 2.8%.
Source: Email 1

Others
- Aptiv (APTV): Buy, PT USD 72
Julius Baer initiates coverage.
Source: Email 3
"""
    items = LLMService._parse_detailed_text(text)
    assert len(items) == 2
    assert items[0]["category"] == "Macro"
    assert items[0]["headline"] == "US CPI: 2.4% YoY"
    assert items[1]["category"] == "Others"
    assert items[1]["source_email_index"] == 2


def test_parse_detailed_text_empty():
    """Parser returns empty list for empty/unparseable text."""
    assert LLMService._parse_detailed_text("") == []
    assert LLMService._parse_detailed_text("Just some random text") == []
