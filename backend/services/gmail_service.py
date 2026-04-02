"""Gmail API service for OAuth2 and email operations."""

import logging
from typing import Optional, List, Dict, Any

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from core.config import settings

logger = logging.getLogger(__name__)


class GmailService:
    """Service for managing Gmail OAuth2 and email operations."""

    def __init__(self):
        """Initialize Gmail service."""
        self.scopes = settings.GMAIL_SCOPES

    def get_auth_url(self, state: str) -> str:
        """
        Generate Gmail OAuth2 authorization URL.

        Args:
            state: State parameter for CSRF protection

        Returns:
            Authorization URL
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                scopes=self.scopes,
            )
            flow.run_local_server(
                port=0, authorization_prompt="force", state_string=state
            )
            return flow.authorization_url(state=state)[0]
        except FileNotFoundError:
            logger.error("credentials.json not found")
            # Generate URL manually for testing/production
            auth_url = (
                f"https://accounts.google.com/o/oauth2/v2/auth?"
                f"client_id={settings.GMAIL_CLIENT_ID}&"
                f"redirect_uri={settings.GMAIL_REDIRECT_URI}&"
                f"response_type=code&"
                f"scope={' '.join(self.scopes)}&"
                f"state={state}&"
                f"access_type=offline&"
                f"prompt=consent"
            )
            return auth_url

    def exchange_code_for_token(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access and refresh tokens.

        Args:
            code: Authorization code from OAuth2 callback

        Returns:
            Dictionary with token information
        """
        try:
            import requests as req

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "code": code,
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "redirect_uri": settings.GMAIL_REDIRECT_URI,
                "grant_type": "authorization_code",
            }

            response = req.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            raise

    def refresh_access_token(self, refresh_token: str) -> Dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Refresh token

        Returns:
            Dictionary with new token information
        """
        try:
            import requests as req

            token_url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": settings.GMAIL_CLIENT_ID,
                "client_secret": settings.GMAIL_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            }

            response = req.post(token_url, data=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Error refreshing access token: {e}")
            raise

    def build_service(self, access_token: str) -> Any:
        """
        Build Gmail API service with access token.

        Args:
            access_token: Gmail access token

        Returns:
            Gmail API service object
        """
        try:
            credentials = Credentials(token=access_token)
            service = build("gmail", "v1", credentials=credentials)
            return service
        except Exception as e:
            logger.error(f"Error building Gmail service: {e}")
            raise

    def build_search_query(
        self, sender_filters: List[str], keyword_filters: List[str], scan_hours: int = 48
    ) -> str:
        """
        Build Gmail search query from filters.

        Args:
            sender_filters: List of sender email addresses
            keyword_filters: List of keywords to search
            scan_hours: How many hours back to scan (converted to days, rounded up)

        Returns:
            Gmail search query string
        """
        import math

        query_parts = []

        # Add sender filters
        if sender_filters:
            sender_query = " OR ".join([f"from:{sender}" for sender in sender_filters])
            query_parts.append(f"({sender_query})")

        # Add keyword filters
        if keyword_filters:
            keyword_query = " OR ".join(keyword_filters)
            query_parts.append(f"({keyword_query})")

        # Combine with AND logic
        query = " AND ".join(query_parts) if query_parts else ""

        # Convert hours to days (Gmail newer_than only supports days)
        days = max(1, math.ceil(scan_hours / 24))
        time_filter = f"newer_than:{days}d"

        if query:
            query += f" {time_filter}"
        else:
            query = time_filter

        logger.debug(f"Built search query: {query}")
        return query

    def fetch_emails(
        self,
        service: Any,
        query: str,
        max_results: int = 10,
        extract_images: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Fetch emails from Gmail.

        Args:
            service: Gmail API service object
            query: Gmail search query
            max_results: Maximum number of emails to fetch

        Returns:
            List of email data
        """
        try:
            # Get email message IDs
            results = service.users().messages().list(
                userId="me", q=query, maxResults=max_results
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                logger.info("No emails found matching query")
                return []

            # Get full message data
            emails = []
            for message in messages:
                try:
                    msg = (
                        service.users()
                        .messages()
                        .get(userId="me", id=message["id"], format="full")
                        .execute()
                    )

                    email_data = self._parse_email(msg, service if extract_images else None)
                    emails.append(email_data)
                except HttpError as e:
                    logger.error(f"Error fetching message {message['id']}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error: {e}")
            raise

    def _parse_email(self, message: Dict[str, Any], service: Any = None) -> Dict[str, Any]:
        """
        Parse email message from Gmail API response.

        Args:
            message: Email message from Gmail API

        Returns:
            Parsed email data
        """
        try:
            headers = message["payload"]["headers"]
            header_dict = {h["name"]: h["value"] for h in headers}

            subject = header_dict.get("Subject", "(No Subject)")
            sender = header_dict.get("From", "Unknown")
            date = header_dict.get("Date", "")

            # Extract email body — search recursively for text parts
            body = self._extract_body(message["payload"])

            # Extract inline images / chart attachments
            images = []
            if service:
                images = self._extract_images(message, service)

            return {
                "id": message["id"],
                "subject": subject,
                "sender": sender,
                "date": date,
                "body": body[:8000],
                "images": images,
            }

        except Exception as e:
            logger.error(f"Error parsing email: {e}")
            return {
                "id": message.get("id", "unknown"),
                "subject": "(Parsing Error)",
                "sender": "Unknown",
                "date": "",
                "body": "",
            }

    def _extract_images(self, message: Dict[str, Any], service: Any) -> List[Dict[str, Any]]:
        """
        Extract inline images and chart attachments from an email.
        Skips images smaller than 5 KB (logos, dividers) and returns at most 3 per email
        (the largest ones, which are most likely to be charts).
        """
        import base64

        msg_id = message["id"]
        candidates = []

        def collect(payload: Dict[str, Any]) -> None:
            mime = payload.get("mimeType", "")
            if mime.startswith("image/"):
                body = payload.get("body", {})
                att_id = body.get("attachmentId")
                size = body.get("size", 0)
                filename = payload.get("filename") or f"image.{mime.split('/')[-1]}"
                if att_id and size >= 5000:
                    candidates.append({
                        "attachment_id": att_id,
                        "filename": filename,
                        "mime_type": mime,
                        "size": size,
                    })
            for part in payload.get("parts", []):
                collect(part)

        collect(message["payload"])

        # Sort by size descending, take top 3 (most likely to be charts, not logos)
        candidates.sort(key=lambda x: x["size"], reverse=True)
        images = []
        for c in candidates[:3]:
            try:
                att = service.users().messages().attachments().get(
                    userId="me", messageId=msg_id, id=c["attachment_id"]
                ).execute()
                data = base64.urlsafe_b64decode(att["data"])
                images.append({
                    "filename": c["filename"],
                    "mime_type": c["mime_type"],
                    "data": data,
                    "size": c["size"],
                })
                logger.info(f"Extracted image {c['filename']} ({len(data)} bytes) from message {msg_id}")
            except Exception as e:
                logger.error(f"Failed to fetch image {c['filename']}: {e}")

        return images

    def _extract_body(self, payload: Dict[str, Any]) -> str:
        """
        Recursively extract plain text body from a MIME payload.
        Prefers text/plain; falls back to text/html with tags stripped.
        """
        import base64
        import re

        mime_type = payload.get("mimeType", "")

        # Leaf node with data
        if "data" in payload.get("body", {}):
            raw = base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace")
            if mime_type == "text/plain":
                return raw
            if mime_type == "text/html":
                # Strip HTML tags for readable plain text
                text = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
                text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"[ \t]+", " ", text)
                text = re.sub(r"\n{3,}", "\n\n", text)
                return text.strip()
            return ""

        parts = payload.get("parts", [])

        # For multipart/alternative prefer text/plain over text/html
        if mime_type == "multipart/alternative":
            plain = next((p for p in parts if p.get("mimeType") == "text/plain"), None)
            html = next((p for p in parts if p.get("mimeType") == "text/html"), None)
            for candidate in [plain, html]:
                if candidate:
                    result = self._extract_body(candidate)
                    if result:
                        return result
            return ""

        # For multipart/mixed and others, recurse into each part and concatenate text
        texts = []
        for part in parts:
            result = self._extract_body(part)
            if result:
                texts.append(result)
        return "\n\n".join(texts)

    def get_user_email(self, service: Any) -> Optional[str]:
        """
        Get authenticated user's email address.

        Args:
            service: Gmail API service object

        Returns:
            User's email address
        """
        try:
            profile = service.users().getProfile(userId="me").execute()
            return profile.get("emailAddress")
        except HttpError as e:
            logger.error(f"Error getting user profile: {e}")
            return None

    def mark_as_read(self, service: Any, message_ids: List[str]) -> bool:
        """
        Mark messages as read in Gmail.

        Args:
            service: Gmail API service object
            message_ids: List of message IDs to mark as read

        Returns:
            Success status
        """
        try:
            for msg_id in message_ids:
                service.users().messages().modify(
                    userId="me", id=msg_id, body={"removeLabelIds": ["UNREAD"]}
                ).execute()
            logger.info(f"Marked {len(message_ids)} messages as read")
            return True
        except HttpError as e:
            logger.error(f"Error marking messages as read: {e}")
            return False
