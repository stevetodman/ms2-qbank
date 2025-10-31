"""Authentication utilities for the review API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from fastapi import Depends, HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents an authenticated principal interacting with the API."""

    identity: str
    roles: Tuple[str, ...]


class AnonymousUser(AuthenticatedUser):
    """Placeholder user used until an identity provider is integrated."""

    def __init__(self) -> None:
        super().__init__(identity="anonymous", roles=())


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Stub middleware that can be replaced with a real authenticator."""

    def __init__(self, app, *, resolver=None):
        super().__init__(app)
        self._resolver = resolver or (lambda request: AnonymousUser())

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        user = self._resolver(request)
        request.state.user = user
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> AuthenticatedUser:
    """Resolve the authenticated user for the current request."""

    user = getattr(request.state, "user", None)
    if isinstance(user, AuthenticatedUser):
        return user
    raise HTTPException(status_code=401, detail="Authentication required")


def require_roles(*roles: str):
    """Dependency factory ensuring the authenticated user has one of *roles*."""

    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not roles or any(role in user.roles for role in roles):
            return user
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return dependency
