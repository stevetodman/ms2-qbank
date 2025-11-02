#!/usr/bin/env python3
"""Validate environment configuration and secrets for MS2 QBank.

This script can be run to verify that all required secrets are configured
properly before deploying or starting services.

Usage:
    python scripts/validate_secrets.py

Exit codes:
    0 - All validations passed
    1 - Validation failed
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from config import validate_startup  # noqa: E402


def main() -> int:
    """Run all configuration validations.

    Returns:
        Exit code (0 for success, 1 for failure)
    """
    print("=" * 60)
    print("MS2 QBank Secrets Validation")
    print("=" * 60)
    print()

    try:
        config = validate_startup()

        print()
        print("=" * 60)
        print("✅ All validations passed!")
        print("=" * 60)
        print()
        print("Configuration summary:")
        print(f"  Environment: {config.environment}")
        print(f"  Debug mode: {config.debug}")
        print(f"  JWT issuer: {config.jwt.issuer}")
        print(f"  JWT audience: {config.jwt.audience}")
        print(f"  JWT secret: {'*' * len(config.jwt.secret)} ({len(config.jwt.secret)} chars)")
        print(f"  Access token TTL: {config.jwt.access_token_expire_minutes} minutes")
        print(f"  Refresh token TTL: {config.jwt.refresh_token_expire_days} days")
        print()
        print("Services can start safely.")
        return 0

    except SystemExit as e:
        # Validation failed, error message already printed by config module
        return e.code if isinstance(e.code, int) else 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
