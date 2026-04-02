"""Service for sending digests to various communication channels."""

import logging
from typing import Optional, Dict, Any

from models.models import ChannelType

logger = logging.getLogger(__name__)


class ChannelService:
    """Service for managing multi-channel message delivery."""

    MAX_MESSAGE_LENGTH = 4000  # Safe limit for most platforms

    def __init__(self):
        """Initialize channel service."""
        self.twilio_client = None
        self.telegram_client = None

    def send_message(
        self, channel_type: ChannelType, message: str, config: Dict[str, Any]
    ) -> bool:
        """
        Send message to specified channel.

        Args:
            channel_type: Type of channel
            message: Message text
            config: Channel configuration

        Returns:
            Success status
        """
        try:
            if channel_type == ChannelType.WHATSAPP:
                return self._send_whatsapp(message, config)
            elif channel_type == ChannelType.TELEGRAM:
                return self._send_telegram(message, config)
            elif channel_type == ChannelType.DISCORD:
                return self._send_discord(message, config)
            elif channel_type == ChannelType.EMAIL:
                return self._send_email(message, config)
            else:
                logger.warning(f"Unknown channel type: {channel_type}")
                return False
        except Exception as e:
            logger.error(f"Error sending message via {channel_type}: {e}")
            return False

    def _split_message(self, message: str, max_length: int = MAX_MESSAGE_LENGTH) -> list[str]:
        """
        Split long message into chunks.

        Args:
            message: Message text
            max_length: Maximum chunk length

        Returns:
            List of message chunks
        """
        if len(message) <= max_length:
            return [message]

        chunks = []
        current_chunk = ""

        for paragraph in message.split("\n"):
            if len(current_chunk) + len(paragraph) + 1 <= max_length:
                current_chunk += paragraph + "\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.rstrip())
                current_chunk = paragraph + "\n"

        if current_chunk:
            chunks.append(current_chunk.rstrip())

        return chunks

    def _send_whatsapp(self, message: str, config: Dict[str, Any]) -> bool:
        """
        Send message via WhatsApp using Twilio.

        Args:
            message: Message text
            config: Configuration with phone_number

        Returns:
            Success status
        """
        try:
            from core.config import settings

            if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN:
                logger.warning("Twilio credentials not configured")
                return False

            from twilio.rest import Client

            client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
            phone_number = config.get("phone_number")

            if not phone_number:
                logger.error("Phone number not provided in config")
                return False

            # Split message if needed
            chunks = self._split_message(message)

            for chunk in chunks:
                client.messages.create(
                    from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
                    body=chunk,
                    to=f"whatsapp:{phone_number}",
                )

            logger.info(
                f"Sent WhatsApp message to {phone_number} ({len(chunks)} chunks)"
            )
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return False

    def send_telegram_document(
        self, caption: str, pdf_bytes: bytes, filename: str, config: Dict[str, Any]
    ) -> bool:
        """
        Send an executive summary text message followed by a PDF document via Telegram.

        Args:
            caption: Executive summary text (sent first as a message)
            pdf_bytes: PDF file content
            filename: Filename for the PDF attachment
            config: Channel config with chat_id

        Returns:
            Success status
        """
        try:
            from core.config import settings

            if not settings.TELEGRAM_BOT_TOKEN:
                logger.warning("Telegram bot token not configured")
                return False

            import requests

            chat_id = config.get("chat_id")
            if not chat_id:
                logger.error("Chat ID not provided in config")
                return False

            base_url = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"

            # Step 1: send executive summary as a text message
            chunks = self._split_message(caption)
            for chunk in chunks:
                resp = requests.post(
                    f"{base_url}/sendMessage",
                    json={"chat_id": chat_id, "text": chunk, "parse_mode": "HTML"},
                    timeout=10,
                )
                resp.raise_for_status()

            # Step 2: send PDF as document (charts are embedded inside)
            resp = requests.post(
                f"{base_url}/sendDocument",
                data={"chat_id": chat_id},
                files={"document": (filename, pdf_bytes, "application/pdf")},
                timeout=30,
            )
            resp.raise_for_status()

            logger.info(f"Sent Telegram executive summary + PDF to {chat_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending Telegram document: {e}")
            return False

    def _send_telegram(self, message: str, config: Dict[str, Any]) -> bool:
        """
        Send message via Telegram.

        Args:
            message: Message text
            config: Configuration with chat_id

        Returns:
            Success status
        """
        try:
            from core.config import settings

            if not settings.TELEGRAM_BOT_TOKEN:
                logger.warning("Telegram bot token not configured")
                return False

            import requests

            chat_id = config.get("chat_id")
            if not chat_id:
                logger.error("Chat ID not provided in config")
                return False

            # Split message if needed
            chunks = self._split_message(message)

            url = (
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
            )

            for chunk in chunks:
                payload = {
                    "chat_id": chat_id,
                    "text": chunk,
                    "parse_mode": "HTML",
                }
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()

            logger.info(f"Sent Telegram message to {chat_id} ({len(chunks)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False

    def _send_discord(self, message: str, config: Dict[str, Any]) -> bool:
        """
        Send message via Discord webhook.

        Args:
            message: Message text
            config: Configuration with webhook_url

        Returns:
            Success status
        """
        try:
            webhook_url = config.get("webhook_url") or None
            from core.config import settings

            if not webhook_url:
                webhook_url = settings.DISCORD_WEBHOOK_URL

            if not webhook_url:
                logger.warning("Discord webhook URL not configured")
                return False

            import requests

            # Split message if needed
            chunks = self._split_message(message)

            for chunk in chunks:
                payload = {"content": chunk}
                response = requests.post(webhook_url, json=payload, timeout=10)
                response.raise_for_status()

            logger.info(f"Sent Discord message ({len(chunks)} chunks)")
            return True

        except Exception as e:
            logger.error(f"Error sending Discord message: {e}")
            return False

    def _send_email(self, message: str, config: Dict[str, Any]) -> bool:
        """
        Send message via email.

        Args:
            message: Message text
            config: Configuration with email address

        Returns:
            Success status
        """
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart

            recipient = config.get("email")
            if not recipient:
                logger.error("Email address not provided in config")
                return False

            # Use environment variables for SMTP settings
            import os

            smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("SMTP_PORT", "587"))
            sender_email = os.getenv("SENDER_EMAIL")
            sender_password = os.getenv("SENDER_PASSWORD")

            if not sender_email or not sender_password:
                logger.warning("SMTP credentials not configured")
                return False

            msg = MIMEMultipart()
            msg["From"] = sender_email
            msg["To"] = recipient
            msg["Subject"] = "Your Email Digest"

            msg.attach(MIMEText(message, "html"))

            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)

            logger.info(f"Sent email to {recipient}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            return False

    def get_channel_display_name(self, channel_type: ChannelType) -> str:
        """
        Get human-readable channel name.

        Args:
            channel_type: Channel type

        Returns:
            Display name
        """
        display_names = {
            ChannelType.WHATSAPP: "WhatsApp",
            ChannelType.TELEGRAM: "Telegram",
            ChannelType.DISCORD: "Discord",
            ChannelType.EMAIL: "Email",
        }
        return display_names.get(channel_type, str(channel_type))

    def validate_channel_config(
        self, channel_type: ChannelType, config: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Validate channel configuration.

        Args:
            channel_type: Channel type
            config: Channel configuration

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            if channel_type == ChannelType.WHATSAPP:
                if "phone_number" not in config:
                    return False, "phone_number is required"
                if not isinstance(config["phone_number"], str):
                    return False, "phone_number must be a string"
                return True, None

            elif channel_type == ChannelType.TELEGRAM:
                if "chat_id" not in config:
                    return False, "chat_id is required"
                if not isinstance(config["chat_id"], (str, int)):
                    return False, "chat_id must be a string or number"
                return True, None

            elif channel_type == ChannelType.DISCORD:
                if "webhook_url" not in config:
                    return False, "webhook_url is required"
                if not isinstance(config["webhook_url"], str):
                    return False, "webhook_url must be a string"
                if not config["webhook_url"].startswith("https://"):
                    return False, "webhook_url must start with https://"
                return True, None

            elif channel_type == ChannelType.EMAIL:
                if "email" not in config:
                    return False, "email is required"
                if not isinstance(config["email"], str):
                    return False, "email must be a string"
                if "@" not in config["email"]:
                    return False, "Invalid email address"
                return True, None

            return False, f"Unknown channel type: {channel_type}"

        except Exception as e:
            return False, str(e)
