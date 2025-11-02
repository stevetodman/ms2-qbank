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
JWT_EXPIRATION_HOURS = 24 * 7  # 7 days
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
