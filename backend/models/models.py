"""SQLAlchemy models for the application."""

from datetime import datetime
from enum import Enum

from sqlalchemy import (
    Column,
    DateTime,
    Enum as SQLEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    Boolean,
    JSON,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class FilterType(str, Enum):
    """Filter type enumeration."""

    SENDER = "sender"
    KEYWORD = "keyword"


class ChannelType(str, Enum):
    """Channel type enumeration."""

    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"


class DigestStatus(str, Enum):
    """Digest execution status enumeration."""

    SUCCESS = "success"
    FAILED = "failed"
    PENDING = "pending"


class DigestConfig(Base):
    """Digest configuration model."""

    __tablename__ = "digest_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    schedule_time = Column(String(5), nullable=False)  # Format: "HH:MM"
    schedule_days = Column(String(50), nullable=False, default="mon,tue,wed,thu,fri")  # Comma-separated: mon,tue,wed,thu,fri,sat,sun
    scan_hours = Column(Integer, nullable=False, default=48)  # How many hours back to scan
    user_id = Column(String(255), nullable=False)  # Gmail user ID
    gmail_access_token = Column(Text, nullable=True)
    gmail_refresh_token = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    filter_rules = relationship(
        "FilterRule", back_populates="digest", cascade="all, delete-orphan"
    )
    channel_configs = relationship(
        "ChannelConfig", back_populates="digest", cascade="all, delete-orphan"
    )
    digest_history = relationship(
        "DigestHistory", back_populates="digest", cascade="all, delete-orphan"
    )


class FilterRule(Base):
    """Email filter rule model."""

    __tablename__ = "filter_rules"

    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(Integer, ForeignKey("digest_configs.id"), nullable=False)
    filter_type = Column(SQLEnum(FilterType), nullable=False)
    value = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    digest = relationship("DigestConfig", back_populates="filter_rules")


class ChannelConfig(Base):
    """Channel configuration model."""

    __tablename__ = "channel_configs"

    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(Integer, ForeignKey("digest_configs.id"), nullable=False)
    channel_type = Column(SQLEnum(ChannelType), nullable=False)
    config = Column(JSON, nullable=True)  # Stores phone numbers, user IDs, etc.
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    digest = relationship("DigestConfig", back_populates="channel_configs")


class DigestHistory(Base):
    """Digest execution history model."""

    __tablename__ = "digest_history"

    id = Column(Integer, primary_key=True, index=True)
    digest_id = Column(Integer, ForeignKey("digest_configs.id"), nullable=False)
    status = Column(SQLEnum(DigestStatus), default=DigestStatus.PENDING)
    email_count = Column(Integer, default=0)
    summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    sent_at = Column(DateTime, nullable=True)
    channel_used = Column(SQLEnum(ChannelType), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    digest = relationship("DigestConfig", back_populates="digest_history")
