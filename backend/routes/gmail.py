"""Routes for Gmail OAuth2 and authentication."""

import json
import logging
import os
import secrets
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core.database import get_db
from models.models import DigestConfig
from schemas.schemas import (
    GmailAuthUrlResponse,
    GlobalGmailAuthUrlResponse,
    GmailCallbackRequest,
    GmailAuthStatus,
    GlobalGmailAuthStatus,
)
from services.gmail_service import GmailService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["gmail"])
gmail_service = GmailService()

# Store OAuth states for CSRF protection
# Values are either a digest_id (int) or the string "global"
oauth_states = {}

GLOBAL_TOKEN_PATH = Path(__file__).parent.parent / "gmail_token.json"
GLOBAL_STATE_MARKER = "global"
FRONTEND_ORIGIN = os.environ.get("FRONTEND_ORIGIN", "http://localhost:5173")


@router.get("/gmail/url", response_model=GlobalGmailAuthUrlResponse)
async def get_global_gmail_auth_url() -> GlobalGmailAuthUrlResponse:
    """
    Generate Gmail OAuth2 authorization URL for global (non-digest-specific) auth.

    Returns:
        Authorization URL
    """
    try:
        state = secrets.token_urlsafe(32)
        oauth_states[state] = GLOBAL_STATE_MARKER
        auth_url = gmail_service.get_auth_url(state)
        logger.info("Generated global Gmail auth URL")
        return GlobalGmailAuthUrlResponse(auth_url=auth_url)
    except Exception as e:
        logger.error(f"Error generating global auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate auth URL",
        )


@router.get("/gmail/status", response_model=GlobalGmailAuthStatus)
@router.get("/status", response_model=GlobalGmailAuthStatus)
async def get_global_gmail_status() -> GlobalGmailAuthStatus:
    """
    Check whether Gmail is connected globally (token file exists).

    Returns:
        Global authentication status
    """
    if GLOBAL_TOKEN_PATH.exists():
        try:
            token_data = json.loads(GLOBAL_TOKEN_PATH.read_text())
            user_email = token_data.get("user_email")
        except Exception:
            user_email = None
        return GlobalGmailAuthStatus(is_authenticated=True, user_email=user_email)
    return GlobalGmailAuthStatus(is_authenticated=False)


@router.get("/gmail/callback")
async def gmail_callback_get(
    code: str,
    state: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Handle Gmail OAuth2 redirect from Google (GET).
    Routes to global token storage or per-digest storage based on state.
    Redirects browser back to the frontend after completion.
    """
    target = oauth_states.pop(state, None)

    try:
        token_data = gmail_service.exchange_code_for_token(code)
    except Exception as e:
        logger.error(f"Token exchange failed: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_ORIGIN}/settings?gmail=error", status_code=302
        )

    if target == GLOBAL_STATE_MARKER or target is None:
        # Store globally in gmail_token.json
        try:
            service = gmail_service.build_service(token_data.get("access_token", ""))
            user_email = gmail_service.get_user_email(service)
        except Exception:
            user_email = None
        payload = {**token_data, "user_email": user_email}
        GLOBAL_TOKEN_PATH.write_text(json.dumps(payload))
        logger.info(f"Stored global Gmail token for {user_email}")
        return RedirectResponse(
            url=f"{FRONTEND_ORIGIN}/settings?gmail=connected", status_code=302
        )

    # Per-digest: store tokens on the digest record
    digest_id = target
    try:
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()
        if not digest:
            return RedirectResponse(
                url=f"{FRONTEND_ORIGIN}/settings?gmail=error", status_code=302
            )
        digest.gmail_access_token = token_data.get("access_token")
        digest.gmail_refresh_token = token_data.get("refresh_token")
        try:
            service = gmail_service.build_service(digest.gmail_access_token)
            digest.user_id = gmail_service.get_user_email(service) or "unknown"
        except Exception:
            pass
        await session.commit()
        logger.info(f"Stored Gmail token for digest {digest_id}")
    except Exception as e:
        logger.error(f"Error storing per-digest token: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_ORIGIN}/settings?gmail=error", status_code=302
        )

    return RedirectResponse(
        url=f"{FRONTEND_ORIGIN}/settings?gmail=connected", status_code=302
    )


@router.get("/gmail/{digest_id}/url", response_model=GmailAuthUrlResponse)
async def get_gmail_auth_url(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> GmailAuthUrlResponse:
    """
    Generate Gmail OAuth2 authorization URL.

    Args:
        digest_id: Digest ID
        session: Database session

    Returns:
        Authorization URL
    """
    try:
        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        if not result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        oauth_states[state] = digest_id

        # Get auth URL
        auth_url = gmail_service.get_auth_url(state)

        logger.info(f"Generated Gmail auth URL for digest {digest_id}")
        return GmailAuthUrlResponse(auth_url=auth_url, digest_id=digest_id)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate auth URL",
        )


@router.post("/gmail/callback")
async def gmail_callback(
    request: GmailCallbackRequest, session: AsyncSession = Depends(get_db)
) -> GmailAuthStatus:
    """
    Handle Gmail OAuth2 callback.

    Args:
        request: Callback request with code
        session: Database session

    Returns:
        Authentication status
    """
    try:
        digest_id = request.digest_id

        # Verify digest exists
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Exchange code for tokens
        token_data = gmail_service.exchange_code_for_token(request.code)

        # Save tokens
        digest.gmail_access_token = token_data.get("access_token")
        digest.gmail_refresh_token = token_data.get("refresh_token")

        # Get user email
        service = gmail_service.build_service(digest.gmail_access_token)
        user_email = gmail_service.get_user_email(service)
        digest.user_id = user_email or "unknown"

        await session.commit()

        logger.info(f"Gmail auth successful for digest {digest_id}: {user_email}")

        return GmailAuthStatus(
            digest_id=digest_id, is_authenticated=True, user_email=user_email
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Gmail callback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to authenticate with Gmail",
        )


@router.get("/gmail/{digest_id}/status", response_model=GmailAuthStatus)
async def get_gmail_auth_status(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> GmailAuthStatus:
    """
    Check Gmail authentication status for a digest.

    Args:
        digest_id: Digest ID
        session: Database session

    Returns:
        Authentication status
    """
    try:
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        is_authenticated = digest.gmail_access_token is not None
        user_email = digest.user_id if is_authenticated else None

        return GmailAuthStatus(
            digest_id=digest_id,
            is_authenticated=is_authenticated,
            user_email=user_email,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking Gmail status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check Gmail status",
        )


@router.post("/gmail/{digest_id}/revoke")
async def revoke_gmail_auth(
    digest_id: int, session: AsyncSession = Depends(get_db)
) -> dict:
    """
    Revoke Gmail authorization for a digest.

    Args:
        digest_id: Digest ID
        session: Database session

    Returns:
        Revocation status
    """
    try:
        stmt = select(DigestConfig).where(DigestConfig.id == digest_id)
        result = await session.execute(stmt)
        digest = result.scalar_one_or_none()

        if not digest:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Digest not found"
            )

        # Clear tokens
        digest.gmail_access_token = None
        digest.gmail_refresh_token = None
        digest.user_id = "default"

        await session.commit()

        logger.info(f"Revoked Gmail auth for digest {digest_id}")

        return {
            "status": "success",
            "message": "Gmail authorization revoked",
            "digest_id": digest_id,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error revoking Gmail auth: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke Gmail authorization",
        )
