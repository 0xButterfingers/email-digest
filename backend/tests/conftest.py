"""Shared test fixtures for email-digest tests."""

import sys
from pathlib import Path

# Add backend to sys.path so imports like `from services.pdf_service import ...` work
sys.path.insert(0, str(Path(__file__).parent.parent))
