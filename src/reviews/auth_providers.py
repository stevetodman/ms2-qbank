"""Authentication providers backed by JWKS endpoints."""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, Iterable, Mapping, MutableMapping, Optional, Sequence

import httpx
import jwt
from fastapi import HTTPException

from .auth import AuthenticatedUser


DEFAULT_ALLOWED_ALGORITHMS = (
    "RS256",
    "RS384",
    "RS512",
    "ES256",
    "ES384",
    "ES512",
    "HS256",
    "HS384",
    "HS512",
)


class TokenValidationError(HTTPException):
    """HTTP error raised when a JWT cannot be validated."""

    def __init__(self, detail: str):
        super().__init__(status_code=401, detail=detail)


JWKSFetcher = Callable[[str], Mapping[str, Iterable[Mapping[str, str]]]]


@dataclass(frozen=True)
class JWKSProviderConfig:
    """Configuration for an issuer backed by a JWKS endpoint."""

    issuer: str
    jwks_url: str
    audience: Optional[str] = None
    subject_claim: str = "sub"
    roles_claim: str = "roles"
    role_mapping: Mapping[str, str] = field(default_factory=dict)
    default_roles: Sequence[str] = field(default_factory=tuple)
    algorithms: Sequence[str] = DEFAULT_ALLOWED_ALGORITHMS


@dataclass
class _JWKSCacheEntry:
    keys: Sequence[Mapping[str, str]]
    fetched_at: datetime


def _default_fetcher(url: str) -> Mapping[str, Iterable[Mapping[str, str]]]:
    with httpx.Client(timeout=5.0) as client:
        response = client.get(url)
        response.raise_for_status()
        payload = response.json()
    if not isinstance(payload, Mapping):
        raise TokenValidationError("Invalid JWKS document")
    return payload


def _decode_oct_key(encoded: str) -> bytes:
    padding = "=" * (-len(encoded) % 4)
    return base64.urlsafe_b64decode(encoded + padding)


def _key_from_jwk(jwk_dict: Mapping[str, str]) -> object:
    kty = jwk_dict.get("kty")
    if kty == "RSA":
        return jwt.algorithms.RSAAlgorithm.from_jwk(json.dumps(jwk_dict))
    if kty == "EC":
        return jwt.algorithms.ECAlgorithm.from_jwk(json.dumps(jwk_dict))
    if kty == "oct":
        key = jwk_dict.get("k")
        if not isinstance(key, str):  # pragma: no cover - defensive
            raise TokenValidationError("JWKS payload missing symmetric key")
        return _decode_oct_key(key)
    raise TokenValidationError("Unsupported key type in JWKS")


def _normalise_roles(raw_roles: Iterable[str] | None, config: JWKSProviderConfig) -> tuple[str, ...]:
    mapped = {role.lower() for role in config.default_roles}
    if not raw_roles:
        return tuple(sorted(mapped))
    for entry in raw_roles:
        canonical = config.role_mapping.get(entry, entry)
        mapped.add(str(canonical).lower())
    return tuple(sorted(mapped))


def jwks_bearer_resolver(
    configs: Sequence[JWKSProviderConfig],
    *,
    fetcher: JWKSFetcher | None = None,
    cache_ttl: timedelta = timedelta(minutes=5),
) -> Callable[[object], AuthenticatedUser]:
    """Return a resolver validating bearer JWTs against JWKS providers."""

    if not configs:
        raise ValueError("At least one JWKS provider must be configured")

    config_by_issuer: Dict[str, JWKSProviderConfig] = {cfg.issuer: cfg for cfg in configs}
    jwks_cache: MutableMapping[str, _JWKSCacheEntry] = {}
    resolve_jwks = fetcher or _default_fetcher

    def _load_keys(config: JWKSProviderConfig, *, force_refresh: bool = False) -> Sequence[Mapping[str, str]]:
        cached = jwks_cache.get(config.issuer)
        now = datetime.now(timezone.utc)
        if not force_refresh and cached and now - cached.fetched_at < cache_ttl:
            return cached.keys

        payload = resolve_jwks(config.jwks_url)
        keys = payload.get("keys") if isinstance(payload, Mapping) else None
        if not isinstance(keys, Iterable):
            raise TokenValidationError("JWKS response missing keys")
        keys_list = [key for key in keys if isinstance(key, Mapping)]
        if not keys_list:
            raise TokenValidationError("No signing keys available for issuer")
        jwks_cache[config.issuer] = _JWKSCacheEntry(keys=keys_list, fetched_at=now)
        return keys_list

    def _select_key(token: str, config: JWKSProviderConfig) -> tuple[object, str]:
        try:
            header = jwt.get_unverified_header(token)
        except jwt.InvalidTokenError as exc:  # pragma: no cover - defensive
            raise TokenValidationError("Invalid token header") from exc

        kid = header.get("kid")
        alg = header.get("alg")

        keys = _load_keys(config)
        matches = [key for key in keys if not kid or key.get("kid") == kid]
        if not matches and kid:
            keys = _load_keys(config, force_refresh=True)
            matches = [key for key in keys if key.get("kid") == kid]

        if not matches:
            raise TokenValidationError("Signing key for token not found")

        jwk_entry = matches[0]
        algorithm = alg or jwk_entry.get("alg")
        if not algorithm:
            algorithm = config.algorithms[0]
        if algorithm not in config.algorithms:
            raise TokenValidationError("Token signed with unsupported algorithm")
        key_obj = _key_from_jwk(jwk_entry)
        return key_obj, algorithm

    def _decode(token: str, config: JWKSProviderConfig) -> AuthenticatedUser:
        key_obj, algorithm = _select_key(token, config)
        try:
            payload = jwt.decode(
                token,
                key_obj,
                algorithms=[algorithm],
                audience=config.audience,
                issuer=config.issuer,
            )
        except jwt.ExpiredSignatureError as exc:
            raise TokenValidationError("Token expired") from exc
        except jwt.InvalidTokenError as exc:
            raise TokenValidationError("Invalid authentication token") from exc

        identity = payload.get(config.subject_claim)
        if not identity:
            raise TokenValidationError("Token subject missing")

        raw_roles = payload.get(config.roles_claim)
        if raw_roles is None:
            roles_iterable: Iterable[str] | None = None
        elif isinstance(raw_roles, (list, tuple, set)):
            roles_iterable = (str(role) for role in raw_roles)
        elif isinstance(raw_roles, str):
            roles_iterable = (role.strip() for role in raw_roles.split(" ") if role.strip())
        else:
            raise TokenValidationError("Invalid roles claim")

        roles = _normalise_roles(roles_iterable, config)
        return AuthenticatedUser(identity=str(identity), roles=roles)

    def _resolve(request) -> AuthenticatedUser:
        header = getattr(request, "headers", {}).get("Authorization")
        if not header or not header.startswith("Bearer "):
            raise TokenValidationError("Authentication required")
        token = header.split(" ", 1)[1].strip()
        if not token:
            raise TokenValidationError("Authentication required")
        try:
            unverified = jwt.decode(token, options={"verify_signature": False})
        except jwt.InvalidTokenError as exc:
            raise TokenValidationError("Invalid authentication token") from exc

        issuer = unverified.get("iss")
        if not issuer or issuer not in config_by_issuer:
            raise TokenValidationError("Unknown token issuer")

        config = config_by_issuer[str(issuer)]
        return _decode(token, config)

    return _resolve


def parse_provider_configs(raw: str) -> list[JWKSProviderConfig]:
    """Parse a JSON document into provider configurations."""

    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:  # pragma: no cover - validated via tests
        raise ValueError("Invalid JWKS provider configuration JSON") from exc

    if isinstance(payload, Mapping):
        payload = [payload]
    if not isinstance(payload, list):
        raise ValueError("JWKS provider configuration must be a list")

    configs: list[JWKSProviderConfig] = []
    for entry in payload:
        if not isinstance(entry, Mapping):
            raise ValueError("Invalid JWKS provider entry")
        role_mapping = entry.get("role_mapping", {})
        default_roles = entry.get("default_roles", ())
        algorithms = entry.get("algorithms")
        try:
            issuer = str(entry["issuer"])
            jwks_url = str(entry["jwks_url"])
        except KeyError as exc:  # pragma: no cover - defensive validation
            raise ValueError("JWKS provider entries require 'issuer' and 'jwks_url'") from exc

        configs.append(
            JWKSProviderConfig(
                issuer=issuer,
                jwks_url=jwks_url,
                audience=entry.get("audience"),
                subject_claim=str(entry.get("subject_claim", "sub")),
                roles_claim=str(entry.get("roles_claim", "roles")),
                role_mapping={str(k): str(v) for k, v in dict(role_mapping).items()},
                default_roles=tuple(str(role) for role in default_roles),
                algorithms=tuple(str(alg) for alg in (algorithms or DEFAULT_ALLOWED_ALGORITHMS)),
            )
        )
    return configs

