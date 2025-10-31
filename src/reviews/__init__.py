"""Review workflow API and persistence utilities."""

from .store import ReviewStore


def create_app(*args, **kwargs):  # type: ignore[override]
    from .app import create_app as _create_app

    return _create_app(*args, **kwargs)


__all__ = ["create_app", "ReviewStore"]
