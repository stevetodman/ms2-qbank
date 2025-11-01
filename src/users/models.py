"""Data models for user authentication and profiles."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, EmailStr, Field
from sqlmodel import Column, DateTime, Field as SQLField, SQLModel


class User(SQLModel, table=True):
    """User account model stored in the database.

    This model represents a medical student user account with authentication
    credentials, profile information, and subscription details.
    """

    __tablename__ = "users"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    email: str = SQLField(unique=True, index=True, max_length=255)
    hashed_password: str = SQLField(max_length=255)

    # Profile information
    full_name: str = SQLField(max_length=255)
    exam_date: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # Subscription details
    subscription_tier: str = SQLField(default="trial", max_length=50)  # trial, 3-month, 6-month, 12-month
    subscription_start: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    subscription_end: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )

    # User preferences
    notification_preferences: str = SQLField(default="{}", max_length=1000)  # JSON string
    display_settings: str = SQLField(default="{}", max_length=1000)  # JSON string

    # Account metadata
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    last_login: Optional[datetime] = SQLField(
        default=None,
        sa_column=Column(DateTime(timezone=True), nullable=True),
    )
    is_active: bool = SQLField(default=True)


class RefreshToken(SQLModel, table=True):
    """Refresh token for JWT authentication.

    Allows users to obtain new access tokens without re-authenticating.
    Tokens can be revoked for security (logout, password change, etc.).
    """

    __tablename__ = "refresh_tokens"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    user_id: int = SQLField(foreign_key="users.id", index=True)
    token: str = SQLField(unique=True, index=True, max_length=500)
    expires_at: datetime = SQLField(
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    created_at: datetime = SQLField(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), nullable=False),
    )
    revoked: bool = SQLField(default=False)
    device_info: Optional[str] = SQLField(default=None, max_length=500)  # User agent for tracking


class UserCreate(BaseModel):
    """Request payload for user registration."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    full_name: str = Field(min_length=1, max_length=255)
    exam_date: Optional[datetime] = None


class UserLogin(BaseModel):
    """Request payload for user login."""

    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Response containing authentication tokens."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = Field(description="Access token expiration time in seconds")


class RefreshTokenRequest(BaseModel):
    """Request payload for refreshing access token."""

    refresh_token: str


class UserProfile(BaseModel):
    """Public user profile information (excludes sensitive data)."""

    id: int
    email: str
    full_name: str
    exam_date: Optional[datetime]
    subscription_tier: str
    subscription_start: Optional[datetime]
    subscription_end: Optional[datetime]
    created_at: datetime
    last_login: Optional[datetime]
    is_active: bool


class UserUpdate(BaseModel):
    """Request payload for updating user profile."""

    full_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    exam_date: Optional[datetime] = None
    notification_preferences: Optional[dict] = None
    display_settings: Optional[dict] = None
