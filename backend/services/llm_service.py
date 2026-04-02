"""Language model service for summarizing emails using Claude."""

import logging
from typing import List, Dict, Any

from anthropic import Anthropic

from core.config import settings

logger = logging.getLogger(__name__)


class LLMService:
    """Service for summarizing emails using Claude."""

    def __init__(self):
        """Initialize LLM service."""
        self.client = Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = "claude-sonnet-4-6"

    def summarize_emails(
        self, emails: List[Dict[str, Any]], digest_name: str = ""
    ) -> Dict[str, str]:
        """
        Summarize a list of emails using Claude.

        Args:
            emails: List of email dictionaries with subject, sender, body
            digest_name: Name of the digest for context

        Returns:
            Dict with keys 'executive' (short Telegram message) and 'detailed' (full PDF content)
        """
        try:
            if not emails:
                empty = "No emails to summarize."
                return {"executive": empty, "detailed": empty}

            formatted_emails = self._format_emails(emails)
            prompt = self._build_summary_prompt(formatted_emails, digest_name)

            message = self.client.messages.create(
                model=self.model,
                max_tokens=4000,
                messages=[{"role": "user", "content": prompt}],
            )

            raw = message.content[0].text
            logger.info(f"Generated summary for {len(emails)} emails")

            # Split on the marker Claude is instructed to include
            if "---DETAILED---" in raw:
                parts = raw.split("---DETAILED---", 1)
                return {
                    "executive": parts[0].strip(),
                    "detailed": parts[1].strip(),
                }

            # Fallback: use full response for both
            return {"executive": raw.strip(), "detailed": raw.strip()}

        except Exception as e:
            logger.error(f"Error summarizing emails: {e}")
            raise

    def _format_emails(self, emails: List[Dict[str, Any]]) -> str:
        """
        Format emails for LLM processing.

        Args:
            emails: List of email dictionaries

        Returns:
            Formatted email text
        """
        formatted = []
        for i, email in enumerate(emails, 1):
            formatted.append(
                f"Email {i}:\n"
                f"From: {email.get('sender', 'Unknown')}\n"
                f"Subject: {email.get('subject', '(No Subject)')}\n"
                f"Date: {email.get('date', 'Unknown')}\n"
                f"Content: {email.get('body', '(No content)')}\n"
            )
        return "\n---\n".join(formatted)

    def _build_summary_prompt(self, formatted_emails: str, digest_name: str) -> str:
        """
        Build the summarization prompt.

        Args:
            formatted_emails: Formatted email text
            digest_name: Digest name for context

        Returns:
            Prompt text
        """
        prompt = (
            "You are a financial research digest assistant. Your ONLY job is to extract and restate "
            "information that is explicitly written in the emails below.\n\n"
            "⚠️ STRICT RULES — follow without exception:\n"
            "1. Use ONLY information found verbatim or directly stated in the provided emails.\n"
            "2. Do NOT add external knowledge, context, opinions, or data from your training.\n"
            "3. Do NOT infer or fill gaps with general market knowledge.\n"
            "4. If a figure (price target, rating, yield, etc.) is not explicitly stated, exclude it.\n"
            "5. If an email has no useful data for a category, omit that category entirely.\n\n"
            "CATEGORIES — classify every item into exactly one of these four:\n"
            "- Macro: macro outlook, GDP, inflation, interest rates, central bank policy, economic indicators\n"
            "- FX: foreign exchange, currency pairs, currency outlook\n"
            "- Bonds: fixed income, credit, sovereign bonds, yields, spreads, duration\n"
            "- Others: equities, commodities, and anything that does not fit the above three\n\n"
            "You must produce TWO sections separated exactly by the line: ---DETAILED---\n\n"
            "=== SECTION 1: EXECUTIVE SUMMARY (before ---DETAILED---) ===\n"
            "A short Telegram message — maximum 10 bullet points total across all categories.\n"
            "Format as Telegram HTML:\n"
            "<b>📊 Daily Bank Reports — Executive Summary</b>\n\n"
            "<b>Macro</b>\n"
            "• [One-line highlight — bank name, key call, single most important figure]\n\n"
            "<b>FX</b>\n"
            "• [One-line highlight — bank name, currency pair, key view or level]\n\n"
            "<b>Bonds</b>\n"
            "• [One-line highlight — bank name, instrument, yield/spread/rating]\n\n"
            "<b>Others</b>\n"
            "• [One-line highlight — bank name, instrument, key call]\n\n"
            "Omit any category heading that has no items.\n\n"
            "=== SECTION 2: FULL DETAILED REPORT (after ---DETAILED---) ===\n"
            "Plain text only (no HTML tags) — this will be rendered in a PDF.\n"
            "Structure — use exactly these headings:\n\n"
            "Macro\n"
            "  - [Instrument/Topic]: [key figure or call]\n"
            "    [2-3 sentences of key points copied closely from the email]\n"
            "    Source: [sender email] | [subject line] | [date]\n\n"
            "FX\n"
            "  - [Currency pair or topic]: [key figure or call]\n"
            "    [2-3 sentences]\n"
            "    Source: [sender email] | [subject line] | [date]\n\n"
            "Bonds\n"
            "  - [Instrument/issuer]: [yield/spread/rating]\n"
            "    [2-3 sentences]\n"
            "    Source: [sender email] | [subject line] | [date]\n\n"
            "Others\n"
            "  - [Instrument/company]: [rating/price target/key figure]\n"
            "    [2-3 sentences]\n"
            "    Source: [sender email] | [subject line] | [date]\n\n"
            "Rules for Section 2:\n"
            "- Every item MUST have a Source line.\n"
            "- Include all explicitly stated figures — copy them exactly as written.\n"
            "- Omit any category that has no items from the emails.\n"
            "- No HTML tags.\n\n"
            f"Emails:\n{formatted_emails}"
        )

        return prompt

    def generate_title(self, emails: List[Dict[str, Any]]) -> str:
        """
        Generate a title for the digest.

        Args:
            emails: List of email dictionaries

        Returns:
            Generated title
        """
        try:
            if not emails:
                return "Email Digest"

            subjects = [email.get("subject", "") for email in emails[:5]]
            subjects_text = ", ".join(subjects)

            prompt = (
                f"Based on these email subjects, generate a short, descriptive title "
                f"(max 10 words) for an email digest:\n"
                f"{subjects_text}\n\n"
                f"Return only the title, nothing else."
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=50,
                messages=[{"role": "user", "content": prompt}],
            )

            title = message.content[0].text.strip()
            logger.info(f"Generated digest title: {title}")
            return title

        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return "Email Digest"

    def extract_action_items(self, emails: List[Dict[str, Any]]) -> List[str]:
        """
        Extract action items from emails.

        Args:
            emails: List of email dictionaries

        Returns:
            List of action items
        """
        try:
            if not emails:
                return []

            formatted_emails = self._format_emails(emails)

            prompt = (
                f"From the following emails, extract ONLY the action items that need to be taken. "
                f"Format as a simple bullet list. If no action items exist, return 'No action items'.\n\n"
                f"Emails:\n{formatted_emails}"
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            action_items = [
                item.strip() for item in response_text.split("\n") if item.strip()
            ]

            logger.info(f"Extracted {len(action_items)} action items")
            return action_items

        except Exception as e:
            logger.error(f"Error extracting action items: {e}")
            return []

    def sentiment_analysis(self, emails: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze sentiment across emails.

        Args:
            emails: List of email dictionaries

        Returns:
            Sentiment analysis results
        """
        try:
            if not emails:
                return {"overall": "neutral", "emails": []}

            formatted_emails = self._format_emails(emails)

            prompt = (
                f"Analyze the sentiment of each email below. "
                f"Classify each as positive, negative, or neutral.\n\n"
                f"Emails:\n{formatted_emails}\n\n"
                f"Return as JSON format: {{'email_1': 'positive', 'email_2': 'negative', ...}}"
            )

            message = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            response_text = message.content[0].text
            logger.info("Completed sentiment analysis")

            return {"overall": "mixed", "analysis": response_text}

        except Exception as e:
            logger.error(f"Error analyzing sentiment: {e}")
            return {"overall": "unknown", "error": str(e)}
