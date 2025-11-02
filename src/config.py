"""Centralized configuration and secrets validation for MS2 QBank.

This module provides configuration management with:
- Environment variable loading and validation
- Secure secret handling
- Development vs production mode detection
- Startup validation to fail fast on misconfiguration
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field, field_validator, ValidationError


class DatabaseConfig(BaseModel):
    """Database configuration settings."""

    users_db: str = Field(default="data/users.db", description="Path to users database")
    analytics_db: str = Field(default="data/analytics.db", description="Path to analytics database")
    videos_db: str = Field(default="data/videos.db", description="Path to videos database")
    flashcards_db: str = Field(default="data/flashcards.db", description="Path to flashcards database")
    assessments_db: str = Field(default="data/assessments.db", description="Path to assessments database")
    library_db: str = Field(default="data/library.db", description="Path to library database")
    planner_db: str = Field(default="data/planner.db", description="Path to planner database")


class JWTConfig(BaseModel):
    """JWT authentication configuration."""

    secret: str = Field(..., min_length=32, description="JWT signing secret (minimum 32 characters)")
    algorithm: str = Field(default="HS256", description="JWT signing algorithm")
    issuer: str = Field(default="ms2-qbank", description="JWT issuer claim")
    audience: str = Field(default="ms2-qbank-api", description="JWT audience claim")
    access_token_expire_minutes: int = Field(default=15, gt=0, description="Access token TTL in minutes")
    refresh_token_expire_days: int = Field(default=7, gt=0, description="Refresh token TTL in days")

    @field_validator("secret")
    @classmethod
    def validate_secret_not_default(cls, v: str) -> str:
        """Ensure JWT secret is not the default development value in production."""
        if v == "dev-secret-key-change-in-production":
            # Check if we're in production mode
            if os.getenv("ENVIRONMENT", "development").lower() in ("production", "prod"):
                raise ValueError(
                    "JWT_SECRET cannot be the default value in production! "
                    "Set a strong random secret via environment variable."
                )
            # In development, issue a warning but allow it
            print(
                "⚠️  WARNING: Using default JWT secret. "
                "This is acceptable for development but MUST be changed in production!",
                file=sys.stderr,
            )
        return v

    @field_validator("secret")
    @classmethod
    def validate_secret_strength(cls, v: str) -> str:
        """Ensure JWT secret has sufficient entropy."""
        if len(v) < 32:
            raise ValueError(f"JWT secret must be at least 32 characters long (got {len(v)})")

        # Check for common weak patterns
        if v.lower() in ("password", "secret", "12345678", "admin"):
            raise ValueError("JWT secret is too weak. Use a cryptographically random string.")

        return v


class Config(BaseModel):
    """Main application configuration."""

    # Environment
    environment: str = Field(default="development", description="Deployment environment")
    debug: bool = Field(default=False, description="Enable debug mode")

    # Database paths
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    # JWT authentication
    jwt: JWTConfig

    # Service ports (for docker-compose)
    users_port: int = Field(default=8001, description="Users service port")
    flashcards_port: int = Field(default=8002, description="Flashcards service port")
    videos_port: int = Field(default=8003, description="Videos service port")
    assessments_port: int = Field(default=8004, description="Assessments service port")
    library_port: int = Field(default=8005, description="Library service port")
    planner_port: int = Field(default=8006, description="Planner service port")
    questions_port: int = Field(default=8007, description="Questions service port")
    reviews_port: int = Field(default=8008, description="Reviews service port")
    analytics_port: int = Field(default=8009, description="Analytics service port")

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Ensure environment is a valid value."""
        valid_envs = ("development", "dev", "staging", "production", "prod", "test")
        if v.lower() not in valid_envs:
            raise ValueError(f"Invalid environment '{v}'. Must be one of: {valid_envs}")
        return v.lower()


def load_config() -> Config:
    """Load configuration from environment variables.

    Returns:
        Config: Validated configuration object

    Raises:
        ValidationError: If required secrets are missing or invalid
        SystemExit: If critical validation fails

    Environment Variables:
        - ENVIRONMENT: Deployment environment (development, production, etc.)
        - DEBUG: Enable debug mode (true/false)
        - JWT_SECRET: JWT signing secret (required, min 32 chars)
        - JWT_ISSUER: JWT issuer claim (optional)
        - JWT_AUDIENCE: JWT audience claim (optional)
        - ACCESS_TOKEN_EXPIRE_MINUTES: Access token TTL (optional)
        - REFRESH_TOKEN_EXPIRE_DAYS: Refresh token TTL (optional)
    """
    # Load JWT configuration from environment
    jwt_secret = os.getenv("JWT_SECRET", "dev-secret-key-change-in-production")

    try:
        config = Config(
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() in ("true", "1", "yes"),
            jwt=JWTConfig(
                secret=jwt_secret,
                algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                issuer=os.getenv("JWT_ISSUER", "ms2-qbank"),
                audience=os.getenv("JWT_AUDIENCE", "ms2-qbank-api"),
                access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15")),
                refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            ),
        )

        # Print configuration summary (without secrets)
        if config.debug:
            print("=" * 60)
            print("MS2 QBank Configuration")
            print("=" * 60)
            print(f"Environment: {config.environment}")
            print(f"Debug: {config.debug}")
            print(f"JWT Issuer: {config.jwt.issuer}")
            print(f"JWT Audience: {config.jwt.audience}")
            print(f"JWT Secret Length: {len(config.jwt.secret)} characters")
            print("=" * 60)

        return config

    except ValidationError as e:
        print("=" * 60, file=sys.stderr)
        print("❌ CONFIGURATION ERROR", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        print("Configuration validation failed. Please check your environment variables:", file=sys.stderr)
        print(file=sys.stderr)
        for error in e.errors():
            field = " -> ".join(str(loc) for loc in error["loc"])
            print(f"  • {field}: {error['msg']}", file=sys.stderr)
        print(file=sys.stderr)
        print("Required environment variables:", file=sys.stderr)
        print("  - JWT_SECRET: Strong random secret (min 32 characters)", file=sys.stderr)
        print(file=sys.stderr)
        print("Optional environment variables:", file=sys.stderr)
        print("  - ENVIRONMENT: development, staging, or production", file=sys.stderr)
        print("  - DEBUG: true or false", file=sys.stderr)
        print("  - JWT_ISSUER: Issuer claim for JWT tokens", file=sys.stderr)
        print("  - JWT_AUDIENCE: Audience claim for JWT tokens", file=sys.stderr)
        print("=" * 60, file=sys.stderr)
        sys.exit(1)


def validate_file_permissions() -> None:
    """Validate that database directory has proper permissions.

    Warns if database files are world-readable or have insecure permissions.
    """
    data_dir = Path("data")
    if not data_dir.exists():
        return

    # Check directory permissions
    stat = data_dir.stat()
    mode = stat.st_mode & 0o777

    # Warn if world-readable
    if mode & 0o004:  # Others have read permission
        print(
            f"⚠️  WARNING: data/ directory is world-readable (permissions: {oct(mode)}). "
            "Consider: chmod 750 data/",
            file=sys.stderr,
        )

    # Check database file permissions
    for db_file in data_dir.glob("*.db"):
        stat = db_file.stat()
        mode = stat.st_mode & 0o777

        if mode & 0o044:  # Group or others have read permission
            print(
                f"⚠️  WARNING: {db_file.name} is group/world-readable (permissions: {oct(mode)}). "
                f"Consider: chmod 600 {db_file}",
                file=sys.stderr,
            )


def check_env_file() -> None:
    """Check if .env file exists and warn if using .env.example."""
    if not Path(".env").exists():
        if Path(".env.example").exists():
            print("⚠️  WARNING: .env file not found. Copy .env.example to .env and configure secrets.", file=sys.stderr)
        else:
            print("⚠️  WARNING: .env file not found. Create .env with required secrets.", file=sys.stderr)


def validate_startup() -> Config:
    """Perform all startup validations.

    This should be called once at application startup.

    Returns:
        Config: Validated configuration

    Raises:
        SystemExit: If validation fails
    """
    check_env_file()
    config = load_config()
    validate_file_permissions()
    return config


__all__ = ["Config", "JWTConfig", "DatabaseConfig", "load_config", "validate_startup"]
