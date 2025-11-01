"""Authentication utilities for the review API."""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Callable, Iterable, Tuple

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from jwt import ExpiredSignatureError, InvalidTokenError
from starlette.middleware.base import BaseHTTPMiddleware

Unauthorized = HTTPException(status_code=401, detail="Authentication required")


@dataclass(frozen=True)
class AuthenticatedUser:
    """Represents an authenticated principal interacting with the API."""

    identity: str
    roles: Tuple[str, ...]


def _ensure_iterable_roles(roles: Iterable[str] | None) -> Tuple[str, ...]:
    if roles is None:
        return ()
    return tuple(str(role).lower() for role in roles)


def bearer_jwt_resolver(
    secret_key: str,
    *,
    algorithms: Tuple[str, ...] = ("HS256",),
    subject_claim: str = "sub",
    roles_claim: str = "roles",
) -> Callable[[Request], AuthenticatedUser]:
    """Build a resolver that authenticates requests using bearer JWTs."""

    def _resolve(request: Request) -> AuthenticatedUser:
        header = request.headers.get("Authorization")
        if not header or not header.startswith("Bearer "):
            raise Unauthorized
        token = header.split(" ", 1)[1].strip()
        if not token:
            raise Unauthorized
        try:
            payload = jwt.decode(token, secret_key, algorithms=list(algorithms))
        except ExpiredSignatureError as exc:
            raise HTTPException(status_code=401, detail="Token expired") from exc
        except InvalidTokenError as exc:
            raise HTTPException(status_code=401, detail="Invalid authentication token") from exc

        identity = payload.get(subject_claim)
        if not identity:
            raise HTTPException(status_code=401, detail="Token subject missing")

        raw_roles = payload.get(roles_claim)
        if raw_roles is not None and not isinstance(raw_roles, (list, tuple, set)):
            raise HTTPException(status_code=401, detail="Invalid roles claim")

        roles = _ensure_iterable_roles(raw_roles)
        return AuthenticatedUser(identity=str(identity), roles=roles)

    return _resolve


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware that resolves the authenticated user for each request."""

    def __init__(self, app, *, resolver: Callable[[Request], AuthenticatedUser]):
        super().__init__(app)
        self._resolver = resolver

    async def dispatch(self, request: Request, call_next):  # type: ignore[override]
        try:
            resolver_result = self._resolver(request)
        except HTTPException as exc:
            return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail}, headers=exc.headers)
        if inspect.isawaitable(resolver_result):
            user = await resolver_result  # pragma: no cover - async resolver not used yet
        else:
            user = resolver_result

        if not isinstance(user, AuthenticatedUser):
            raise HTTPException(status_code=401, detail="Invalid authentication response")

        request.state.user = user
        response = await call_next(request)
        return response


def get_current_user(request: Request) -> AuthenticatedUser:
    """Resolve the authenticated user for the current request."""

    user = getattr(request.state, "user", None)
    if isinstance(user, AuthenticatedUser):
        return user
    raise Unauthorized


def require_roles(*roles: str):
    """Dependency factory ensuring the authenticated user has one of *roles*."""

    required = {_role.lower() for _role in roles}

    def dependency(user: AuthenticatedUser = Depends(get_current_user)) -> AuthenticatedUser:
        if not required or any(role in user.roles for role in required):
            return user
        raise HTTPException(status_code=403, detail="Insufficient permissions")

    return dependency
