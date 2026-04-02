"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field

from models.models import FilterType, ChannelType, DigestStatus


# Filter Rule Schemas
class FilterRuleCreate(BaseModel):
    """Schema for creating a filter rule."""

    filter_type: FilterType
    value: str = Field(..., min_length=1, max_length=255)


class FilterRuleUpdate(BaseModel):
    """Schema for updating a filter rule."""

    filter_type: Optional[FilterType] = None
    value: Optional[str] = Field(None, min_length=1, max_length=255)


class FilterRuleResponse(BaseModel):
    """Schema for filter rule response."""

    id: int
    digest_id: int
    filter_type: FilterType
    value: str
    created_at: datetime

    class Config:
        from_attributes = True


# Channel Config Schemas
class ChannelConfigCreate(BaseModel):
    """Schema for creating a channel config."""

    channel_type: ChannelType
    config: Optional[Dict[str, Any]] = None
    is_primary: bool = False


class ChannelConfigUpdate(BaseModel):
    """Schema for updating a channel config."""

    channel_type: Optional[ChannelType] = None
    config: Optional[Dict[str, Any]] = None
    is_primary: Optional[bool] = None


class ChannelConfigResponse(BaseModel):
    """Schema for channel config response."""

    id: int
    digest_id: int
    channel_type: ChannelType
    config: Optional[Dict[str, Any]]
    is_primary: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Digest Config Schemas
class DigestConfigCreate(BaseModel):
    """Schema for creating a digest config."""

    name: str = Field(..., min_length=1, max_length=255)
    schedule_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    schedule_days: str = Field(default="mon,tue,wed,thu,fri")
    scan_hours: int = Field(default=48, ge=1, le=168)
    is_active: bool = True
    filter_rules: Optional[List[FilterRuleCreate]] = None
    channel_configs: Optional[List[ChannelConfigCreate]] = None


class DigestConfigUpdate(BaseModel):
    """Schema for updating a digest config."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    schedule_time: Optional[str] = Field(None, pattern=r"^\d{2}:\d{2}$")
    schedule_days: Optional[str] = None
    scan_hours: Optional[int] = Field(None, ge=1, le=168)
    is_active: Optional[bool] = None


class DigestConfigResponse(BaseModel):
    """Schema for digest config response."""

    id: int
    name: str
    is_active: bool
    schedule_time: str
    schedule_days: str = "mon,tue,wed,thu,fri"
    scan_hours: int = 48
    user_id: str
    created_at: datetime
    updated_at: datetime
    filter_rules: Optional[List[FilterRuleResponse]] = None
    channel_configs: Optional[List[ChannelConfigResponse]] = None

    class Config:
        from_attributes = True


class DigestConfigDetailResponse(DigestConfigResponse):
    """Detailed digest config response."""

    pass


# Digest History Schemas
class DigestHistoryCreate(BaseModel):
    """Schema for creating digest history."""

    digest_id: int
    status: DigestStatus
    email_count: int = 0
    summary: Optional[str] = None
    error_message: Optional[str] = None
    channel_used: Optional[ChannelType] = None


class DigestHistoryResponse(BaseModel):
    """Schema for digest history response."""

    id: int
    digest_id: int
    status: DigestStatus
    email_count: int
    summary: Optional[str]
    error_message: Optional[str]
    sent_at: Optional[datetime]
    channel_used: Optional[ChannelType]
    created_at: datetime

    class Config:
        from_attributes = True


class DigestRunHistoryItem(BaseModel):
    """Schema for a history item shaped for the frontend."""

    id: int
    status: DigestStatus
    timestamp: Optional[datetime]
    duration: Optional[int]
    emails_processed: int
    emails_sent: int
    error: Optional[str]
    summary: Optional[str]
    channels_count: int

    class Config:
        from_attributes = True


class DigestRunResponse(BaseModel):
    """Schema for a manual digest run response."""

    success: bool
    message: str
    history_id: Optional[int] = None


# Gmail OAuth Schemas
class GmailAuthUrlResponse(BaseModel):
    """Schema for Gmail auth URL response."""

    auth_url: str
    digest_id: int


class GlobalGmailAuthUrlResponse(BaseModel):
    """Schema for global Gmail auth URL response (no digest_id required)."""

    auth_url: str


class GmailCallbackRequest(BaseModel):
    """Schema for Gmail callback."""

    code: str
    digest_id: int


class GmailAuthStatus(BaseModel):
    """Schema for Gmail auth status."""

    digest_id: int
    is_authenticated: bool
    user_email: Optional[str] = None


class GlobalGmailAuthStatus(BaseModel):
    """Schema for global Gmail auth status (no digest_id required)."""

    is_authenticated: bool
    user_email: Optional[str] = None


# Scheduler Schemas
class SchedulerStatus(BaseModel):
    """Schema for scheduler status."""

    is_running: bool
    jobs_count: int
    active_digests: int


class ManualRunRequest(BaseModel):
    """Schema for manual digest run."""

    digest_id: int


class ManualRunResponse(BaseModel):
    """Schema for manual run response."""

    success: bool
    message: str
    history_id: Optional[int] = None
