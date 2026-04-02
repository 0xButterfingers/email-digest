"""Service for orchestrating digest creation and delivery."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from models.models import (
    DigestConfig,
    DigestHistory,
    FilterRule,
    ChannelConfig,
    DigestStatus,
)
from services.gmail_service import GmailService
from services.llm_service import LLMService
from services.channel_service import ChannelService
from services.pdf_service import PdfService

logger = logging.getLogger(__name__)

GLOBAL_TOKEN_PATH = Path(__file__).parent.parent / "gmail_token.json"


class DigestService:
    """Service for orchestrating digest operations."""

    def __init__(self):
        """Initialize digest service."""
        self.gmail_service = GmailService()
        self.llm_service = LLMService()
        self.channel_service = ChannelService()
        self.pdf_service = PdfService()

    async def run_digest(
        self, digest_id: int, session: AsyncSession
    ) -> Optional[DigestHistory]:
        """
        Execute a complete digest workflow.

        Args:
            digest_id: Digest configuration ID
            session: Database session

        Returns:
            DigestHistory record
        """
        history = None
        try:
            # Fetch digest config
            stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
            result = await session.execute(stmt)
            digest = result.scalar_one_or_none()

            if not digest:
                logger.error(f"Digest {digest_id} not found")
                return None

            if not digest.is_active:
                logger.info(f"Digest {digest_id} is not active")
                return None

            # Create history record
            history = DigestHistory(
                digest_id=digest_id, status=DigestStatus.PENDING
            )
            session.add(history)
            await session.flush()

            logger.info(f"Starting digest run for {digest.name}")

            # Step 1: Fetch emails
            emails = await self._fetch_emails(digest, session)
            if not emails:
                logger.info(f"No emails found for digest {digest.name}")
                history.email_count = 0
                history.status = DigestStatus.SUCCESS
                history.sent_at = datetime.utcnow()
                await session.commit()
                return history

            # Step 2: Summarize emails — returns executive + detailed
            summaries = self.llm_service.summarize_emails(emails, digest.name)
            executive_summary = summaries["executive"]
            detailed_summary = summaries["detailed"]
            history.email_count = len(emails)
            history.summary = executive_summary

            # Collect all images across emails (deduplicated by filename)
            all_images = []
            seen_filenames = set()
            for email in emails:
                for img in email.get("images", []):
                    if img["filename"] not in seen_filenames:
                        all_images.append(img)
                        seen_filenames.add(img["filename"])
            logger.info(f"Collected {len(all_images)} images across {len(emails)} emails")

            # Step 3: Generate PDF from detailed summary + images
            run_date = datetime.utcnow().strftime("%Y-%m-%d")
            pdf_filename = f"{digest.name.replace(' ', '_')}_{run_date}.pdf"
            try:
                pdf_bytes = self.pdf_service.generate(
                    detailed_summary, digest.name, images=all_images or None
                )
                logger.info(f"Generated PDF ({len(pdf_bytes)} bytes)")
            except Exception as e:
                logger.error(f"PDF generation failed: {e}")
                pdf_bytes = None

            # Step 4: Send to channels
            channels = await self._get_channels(digest_id, session)
            if not channels:
                logger.warning(f"No channels configured for digest {digest.name}")
                history.status = DigestStatus.SUCCESS
                history.sent_at = datetime.utcnow()
                await session.commit()
                return history

            sent_channel = None
            for channel in channels:
                try:
                    if channel.channel_type.value == "telegram" and pdf_bytes:
                        success = self.channel_service.send_telegram_document(
                            executive_summary, pdf_bytes, pdf_filename,
                            channel.config
                        )
                    else:
                        success = self.channel_service.send_message(
                            channel.channel_type, executive_summary, channel.config
                        )
                    if success:
                        sent_channel = channel.channel_type
                        if channel.is_primary:
                            break
                except Exception as e:
                    logger.error(
                        f"Error sending to {channel.channel_type}: {e}"
                    )
                    continue

            if sent_channel:
                history.channel_used = sent_channel
                history.status = DigestStatus.SUCCESS
                logger.info(
                    f"Digest {digest.name} delivered via {sent_channel.value}"
                )
            else:
                history.status = DigestStatus.FAILED
                history.error_message = "Failed to send via any channel"
                logger.error(f"Failed to deliver digest {digest.name}")

            history.sent_at = datetime.utcnow()
            await session.commit()

            return history

        except Exception as e:
            logger.error(f"Error running digest {digest_id}: {e}")
            if history:
                history.status = DigestStatus.FAILED
                history.error_message = str(e)
                history.sent_at = datetime.utcnow()
                try:
                    await session.commit()
                except Exception as commit_error:
                    logger.error(f"Error committing error state: {commit_error}")
            return history

    async def _fetch_emails(
        self, digest: DigestConfig, session: AsyncSession
    ) -> List[dict]:
        """
        Fetch emails matching digest filters.

        Args:
            digest: Digest configuration
            session: Database session

        Returns:
            List of email data
        """
        try:
            access_token = digest.gmail_access_token
            refresh_token = digest.gmail_refresh_token

            # Fall back to global token if no per-digest token
            if not access_token and GLOBAL_TOKEN_PATH.exists():
                try:
                    global_token = json.loads(GLOBAL_TOKEN_PATH.read_text())
                    access_token = global_token.get("access_token")
                    refresh_token = global_token.get("refresh_token")
                    logger.info(f"Using global Gmail token for digest {digest.name}")
                except Exception as e:
                    logger.error(f"Error reading global Gmail token: {e}")

            if not access_token:
                logger.error(f"No Gmail token for digest {digest.name}")
                return []

            # Refresh token if needed
            if refresh_token:
                try:
                    token_data = self.gmail_service.refresh_access_token(refresh_token)
                    access_token = token_data.get("access_token")
                    # Persist refreshed token back to the global file if that's what we used
                    if not digest.gmail_access_token and GLOBAL_TOKEN_PATH.exists():
                        try:
                            global_token = json.loads(GLOBAL_TOKEN_PATH.read_text())
                            global_token["access_token"] = access_token
                            GLOBAL_TOKEN_PATH.write_text(json.dumps(global_token))
                        except Exception:
                            pass
                    else:
                        digest.gmail_access_token = access_token
                        await session.commit()
                except Exception as e:
                    logger.error(f"Error refreshing Gmail token: {e}")

            # Build Gmail service
            service = self.gmail_service.build_service(access_token)

            # Get filters
            stmt = select(FilterRule).where(FilterRule.digest_id == digest.id)
            result = await session.execute(stmt)
            filter_rules = result.scalars().all()

            # Build search query
            sender_filters = [
                rule.value for rule in filter_rules if rule.filter_type.value == "sender"
            ]
            keyword_filters = [
                rule.value for rule in filter_rules if rule.filter_type.value == "keyword"
            ]

            query = self.gmail_service.build_search_query(
                sender_filters, keyword_filters,
                scan_hours=getattr(digest, "scan_hours", None) or 48,
            )

            # Fetch emails
            emails = self.gmail_service.fetch_emails(service, query, max_results=10)
            logger.info(f"Fetched {len(emails)} emails for digest {digest.name}")
            return emails

        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            return []

    async def _get_channels(
        self, digest_id: int, session: AsyncSession
    ) -> List[ChannelConfig]:
        """
        Get channel configurations for a digest.

        Args:
            digest_id: Digest ID
            session: Database session

        Returns:
            List of channel configurations
        """
        try:
            stmt = select(ChannelConfig).where(
                ChannelConfig.digest_id == digest_id
            )
            result = await session.execute(stmt)
            channels = result.scalars().all()
            return sorted(channels, key=lambda c: c.is_primary, reverse=True)
        except Exception as e:
            logger.error(f"Error fetching channels: {e}")
            return []

    async def get_digest_history(
        self, digest_id: int, limit: int = 10, session: Optional[AsyncSession] = None
    ) -> List[DigestHistory]:
        """
        Get digest execution history.

        Args:
            digest_id: Digest ID
            limit: Maximum records to return
            session: Database session

        Returns:
            List of history records
        """
        try:
            if not session:
                return []

            stmt = (
                select(DigestHistory)
                .where(DigestHistory.digest_id == digest_id)
                .order_by(DigestHistory.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error fetching digest history: {e}")
            return []

    async def update_digest_config(
        self,
        digest_id: int,
        name: Optional[str] = None,
        schedule_time: Optional[str] = None,
        is_active: Optional[bool] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[DigestConfig]:
        """
        Update digest configuration.

        Args:
            digest_id: Digest ID
            name: New digest name
            schedule_time: New schedule time
            is_active: New active status
            session: Database session

        Returns:
            Updated digest config
        """
        try:
            if not session:
                return None

            stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
            result = await session.execute(stmt)
            digest = result.scalar_one_or_none()

            if not digest:
                logger.error(f"Digest {digest_id} not found")
                return None

            if name:
                digest.name = name
            if schedule_time:
                digest.schedule_time = schedule_time
            if is_active is not None:
                digest.is_active = is_active

            digest.updated_at = datetime.utcnow()
            await session.commit()
            logger.info(f"Updated digest {digest_id}")
            return digest

        except Exception as e:
            logger.error(f"Error updating digest: {e}")
            return None
