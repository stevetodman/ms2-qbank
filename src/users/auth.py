"""Authentication utilities for password hashing and JWT token management."""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Optional

import jwt
from passlib.context import CryptContext

# Password hashing configuration using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))  # 15 minutes
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))  # 7 days
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days (legacy, for backwards compatibility)


def hash_password(password: str) -> str:
    """Hash a plain text password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password against a hashed password.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to compare against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(user_id: int, email: str, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token for a user.

    Args:
        user_id: User's database ID
        email: User's email address
        expires_delta: Optional custom expiration time delta

    Returns:
        Encoded JWT token string
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    expire = datetime.now(timezone.utc) + expires_delta

    payload = {
        "sub": str(user_id),  # Subject: user ID
        "email": email,
        "exp": expire,  # Expiration time
        "iat": datetime.now(timezone.utc),  # Issued at
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid
    """
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, ValueError):
        return None


def create_token_pair(user_id: int, email: str) -> dict:
    """Create both access and refresh tokens for a user.

    Args:
        user_id: User's database ID
        email: User's email address

    Returns:
        Dictionary containing:
            - access_token: Short-lived access token (15 min)
            - refresh_token: Long-lived refresh token (7 days)
            - token_type: "bearer"
            - expires_in: Access token expiration in seconds
    """
    # Create short-lived access token (15 minutes)
    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": datetime.now(timezone.utc) + access_expires,
        "iat": datetime.now(timezone.utc),
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Create long-lived refresh token (7 days)
    refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + refresh_expires,
        "iat": datetime.now(timezone.utc),
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "refresh_expires_at": datetime.now(timezone.utc) + refresh_expires,
    }


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token.

    Args:
        token: Refresh token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or not a refresh token
    """
    payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])

    # Verify this is a refresh token
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token is not a refresh token")

    return payload
