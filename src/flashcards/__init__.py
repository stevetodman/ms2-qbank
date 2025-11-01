"""Flashcards microservice exposing deck and card management endpoints."""

from .app import create_app

__all__ = ["create_app"]
