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
JWT_ISSUER = os.getenv("JWT_ISSUER", "ms2-qbank")
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "ms2-qbank-api")


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

    The token includes the following claims for enhanced security:
    - sub: User ID (subject)
    - email: User's email address
    - exp: Expiration time
    - iat: Issued at time
    - nbf: Not before time (same as iat, token valid immediately)
    - iss: Issuer identifier
    - aud: Intended audience
    """
    if expires_delta is None:
        expires_delta = timedelta(hours=JWT_EXPIRATION_HOURS)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    payload = {
        "sub": str(user_id),  # Subject: user ID
        "email": email,
        "exp": expire,  # Expiration time
        "iat": now,  # Issued at
        "nbf": now,  # Not before (valid immediately)
        "iss": JWT_ISSUER,  # Issuer
        "aud": JWT_AUDIENCE,  # Audience
    }

    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token.

    Validates all standard claims including:
    - exp: Token must not be expired
    - nbf: Token must not be used before its valid time
    - iss: Token must be issued by the expected issuer
    - aud: Token must be intended for the expected audience

    Args:
        token: JWT token string to decode

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.ImmatureSignatureError: If token is not yet valid (nbf)
        jwt.InvalidIssuerError: If token issuer doesn't match
        jwt.InvalidAudienceError: If token audience doesn't match
        jwt.InvalidTokenError: If token is otherwise invalid
    """
    return jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
            "require": ["exp", "iat", "nbf", "iss", "aud", "sub"],
        },
    )


def get_user_id_from_token(token: str) -> Optional[int]:
    """Extract user ID from a JWT token.

    Args:
        token: JWT token string

    Returns:
        User ID if token is valid, None otherwise

    Note:
        Returns None for any invalid token (expired, immature, wrong issuer/audience, etc.)
    """
    try:
        payload = decode_access_token(token)
        user_id = payload.get("sub")
        return int(user_id) if user_id else None
    except (
        jwt.ExpiredSignatureError,
        jwt.ImmatureSignatureError,
        jwt.InvalidIssuerError,
        jwt.InvalidAudienceError,
        jwt.InvalidTokenError,
        ValueError,
    ):
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
    now = datetime.now(timezone.utc)

    # Create short-lived access token (15 minutes)
    access_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_payload = {
        "sub": str(user_id),
        "email": email,
        "type": "access",
        "exp": now + access_expires,
        "iat": now,
        "nbf": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    access_token = jwt.encode(access_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    # Create long-lived refresh token (7 days)
    refresh_expires = timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_payload = {
        "sub": str(user_id),
        "type": "refresh",
        "exp": now + refresh_expires,
        "iat": now,
        "nbf": now,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
    }
    refresh_token = jwt.encode(refresh_payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
        "refresh_expires_at": now + refresh_expires,
    }


def decode_refresh_token(token: str) -> dict:
    """Decode and validate a refresh token.

    Validates all standard claims including issuer and audience.

    Args:
        token: Refresh token string

    Returns:
        Decoded token payload

    Raises:
        jwt.ExpiredSignatureError: If token has expired
        jwt.InvalidTokenError: If token is invalid or not a refresh token
    """
    payload = jwt.decode(
        token,
        JWT_SECRET,
        algorithms=[JWT_ALGORITHM],
        issuer=JWT_ISSUER,
        audience=JWT_AUDIENCE,
        options={
            "verify_signature": True,
            "verify_exp": True,
            "verify_nbf": True,
            "verify_iat": True,
            "verify_aud": True,
            "verify_iss": True,
        },
    )

    # Verify this is a refresh token
    if payload.get("type") != "refresh":
        raise jwt.InvalidTokenError("Token is not a refresh token")

    return payload
