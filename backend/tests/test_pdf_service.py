"""Tests for PdfService executive layout with footnotes."""

import re
from io import BytesIO
from services.pdf_service import PdfService, _extract_sender_name, _s


SAMPLE_ITEMS = [
    {
        "category": "Macro",
        "headline": "US CPI — March print at 2.4% YoY",
        "body": "Core CPI fell to 2.8% from 3.0%. Markets pricing 3 cuts.",
        "source_email_index": 0,
    },
    {
        "category": "Macro",
        "headline": "China PMI — Manufacturing at 51.2",
        "body": "New export orders rose to 50.8. Stimulus showing through.",
        "source_email_index": 1,
    },
    {
        "category": "FX",
        "headline": "EUR/USD — Rallied to 1.0920 post-CPI",
        "body": "Dollar weakness broad-based. DXY broke below 104.",
        "source_email_index": 0,
    },
]

SAMPLE_EMAILS = [
    {
        "id": "msg_001",
        "gmail_message_id": "msg_001",
        "sender": "JP Morgan Research <research@jpmorgan.com>",
        "subject": "US CPI: Disinflation Resumes",
        "date": "Thu, 10 Apr 2026 08:15:00 +0800",
    },
    {
        "id": "msg_002",
        "gmail_message_id": "msg_002",
        "sender": "Goldman Sachs <asia@gs.com>",
        "subject": "China: Green Shoots Confirmed",
        "date": "Thu, 10 Apr 2026 07:42:00 +0800",
    },
]

SAMPLE_ARCHIVE_URLS = {
    "msg_001": "/msg_001/",
    "msg_002": "/msg_002/",
}

ARCHIVE_BASE = "https://archive.0xbutterfingers.xyz"


def test_generate_returns_pdf_bytes():
    svc = PdfService()
    pdf_bytes = svc.generate(
        items=SAMPLE_ITEMS,
        emails=SAMPLE_EMAILS,
        archive_urls=SAMPLE_ARCHIVE_URLS,
        digest_name="Daily Bank Reports",
        archive_base_url=ARCHIVE_BASE,
    )
    assert isinstance(pdf_bytes, bytes)
    assert pdf_bytes[:5] == b"%PDF-"
    assert len(pdf_bytes) > 500


def test_generate_with_empty_items():
    svc = PdfService()
    pdf_bytes = svc.generate(
        items=[],
        emails=[],
        archive_urls={},
        digest_name="Empty Digest",
        archive_base_url=ARCHIVE_BASE,
    )
    assert pdf_bytes[:5] == b"%PDF-"


def test_multiple_items_same_email_share_footnote():
    svc = PdfService()
    items, footnotes = svc._build_footnotes(SAMPLE_ITEMS, SAMPLE_EMAILS, SAMPLE_ARCHIVE_URLS, ARCHIVE_BASE)
    assert items[0]["footnote_num"] == items[2]["footnote_num"]  # both from email 0
    assert items[1]["footnote_num"] != items[0]["footnote_num"]  # email 1 is different
    assert len(footnotes) == 2  # only 2 unique sources


def test_extract_sender_name():
    assert _extract_sender_name("JP Morgan Research <research@jpmorgan.com>") == "JP Morgan Research"
    assert _extract_sender_name("research@jpmorgan.com") == "research@jpmorgan.com"
    assert _extract_sender_name("Unknown") == "Unknown"
