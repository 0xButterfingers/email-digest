"""Tests for LLM service structured JSON output."""

import json
from unittest.mock import MagicMock, patch
from services.llm_service import LLMService


MOCK_EXECUTIVE = '<b>📊 Daily Bank Reports — Executive Summary</b>\n\n<b>Macro</b>\n• JPM: US CPI at 2.4% YoY'

MOCK_DETAILED_JSON = json.dumps([
    {
        "category": "Macro",
        "headline": "US CPI — March print at 2.4% YoY",
        "body": "Core CPI fell to 2.8% from 3.0%. Markets pricing 3 cuts by year-end.",
        "source_email_index": 0,
    },
    {
        "category": "FX",
        "headline": "EUR/USD — Rallied to 1.0920 post-CPI",
        "body": "Dollar weakness broad-based. DXY broke below 104.",
        "source_email_index": 1,
    },
])


def _make_mock_response(text):
    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text=text)]
    return mock_msg


def test_summarize_returns_detailed_items_as_list():
    """When LLM returns valid JSON after ---DETAILED---, detailed_items is a list of dicts."""
    svc = LLMService.__new__(LLMService)
    svc.client = MagicMock()
    svc.model = "claude-sonnet-4-6"

    raw_response = f"{MOCK_EXECUTIVE}\n\n---DETAILED---\n\n{MOCK_DETAILED_JSON}"
    svc.client.messages.create.return_value = _make_mock_response(raw_response)

    result = svc.summarize_emails(
        [{"sender": "a@test.com", "subject": "Test", "date": "2026-04-10", "body": "content"}],
        "Test Digest",
    )

    assert "detailed_items" in result, "result must contain 'detailed_items' key"
    assert isinstance(result["detailed_items"], list)
    assert len(result["detailed_items"]) == 2
    assert result["detailed_items"][0]["category"] == "Macro"
    assert result["detailed_items"][0]["source_email_index"] == 0
    assert result["executive"] == MOCK_EXECUTIVE


def test_summarize_handles_json_with_code_fences():
    """LLM sometimes wraps JSON in ```json ... ``` — parsing should handle this."""
    svc = LLMService.__new__(LLMService)
    svc.client = MagicMock()
    svc.model = "claude-sonnet-4-6"

    fenced = f"```json\n{MOCK_DETAILED_JSON}\n```"
    raw_response = f"{MOCK_EXECUTIVE}\n\n---DETAILED---\n\n{fenced}"
    svc.client.messages.create.return_value = _make_mock_response(raw_response)

    result = svc.summarize_emails(
        [{"sender": "a@test.com", "subject": "Test", "date": "2026-04-10", "body": "content"}],
        "Test Digest",
    )

    assert "detailed_items" in result
    assert len(result["detailed_items"]) == 2


def test_summarize_falls_back_on_invalid_json():
    """When LLM returns non-JSON after ---DETAILED---, fall back to plain text."""
    svc = LLMService.__new__(LLMService)
    svc.client = MagicMock()
    svc.model = "claude-sonnet-4-6"

    raw_response = f"{MOCK_EXECUTIVE}\n\n---DETAILED---\n\nMacro\n  - US CPI at 2.4%\n    Source: JPM"
    svc.client.messages.create.return_value = _make_mock_response(raw_response)

    result = svc.summarize_emails(
        [{"sender": "a@test.com", "subject": "Test", "date": "2026-04-10", "body": "content"}],
        "Test Digest",
    )

    # Should fall back — no detailed_items, has 'detailed' key instead
    assert "detailed" in result
    assert "detailed_items" not in result
