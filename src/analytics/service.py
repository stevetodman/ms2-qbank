"""Service wrapper managing analytics scheduling and health monitoring."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

from .scheduler import AnalyticsRefreshScheduler

_DEFAULT_ARTIFACT_DIR = Path(__file__).resolve().parents[2] / "data" / "analytics"
_DEFAULT_FRESHNESS_WINDOW = timedelta(minutes=10)
_DEFAULT_CHECK_INTERVAL = timedelta(minutes=1)


def _parse_timestamp(value: str) -> Optional[datetime]:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed.astimezone(timezone.utc)


@dataclass
class AnalyticsHealth:
    """Container describing analytics freshness state."""

    generated_at: Optional[datetime]
    is_fresh: bool

    def as_json(self) -> dict[str, Optional[str] | bool]:
        timestamp = (
            self.generated_at.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
            if self.generated_at
            else None
        )
        return {"generated_at": timestamp, "is_fresh": self.is_fresh}


class AnalyticsService:
    """Background worker providing analytics health insights and scheduling."""

    def __init__(
        self,
        scheduler: Optional[AnalyticsRefreshScheduler] = None,
        *,
        artifact_dir: Path | str = _DEFAULT_ARTIFACT_DIR,
        freshness_window: timedelta = _DEFAULT_FRESHNESS_WINDOW,
        check_interval: timedelta = _DEFAULT_CHECK_INTERVAL,
    ) -> None:
        self._scheduler = scheduler or AnalyticsRefreshScheduler()
        self._artifact_dir = Path(artifact_dir)
        self._freshness_window = freshness_window
        self._check_interval = check_interval

        self._monitor_task: Optional[asyncio.Task[None]] = None
        self._stale_reported = False

        self.router = APIRouter(prefix="/analytics")

        @self.router.get("/health")
        def _health_endpoint() -> dict[str, Optional[str] | bool]:
            return self.current_health().as_json()

    @property
    def scheduler(self) -> AnalyticsRefreshScheduler:
        return self._scheduler

    async def start(self) -> None:
        await self._scheduler.start()
        self._monitor_task = asyncio.create_task(self._monitor_freshness())

    async def shutdown(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await self._scheduler.shutdown()

    async def handle_status_change(self, *args: object, **kwargs: object) -> None:
        await self._scheduler.handle_status_change(*args, **kwargs)

    def current_health(self) -> AnalyticsHealth:
        latest = self._latest_snapshot_timestamp()
        now = datetime.now(timezone.utc)
        is_fresh = bool(latest and now - latest <= self._freshness_window)
        return AnalyticsHealth(generated_at=latest, is_fresh=is_fresh)

    async def _monitor_freshness(self) -> None:
        try:
            while True:
                try:
                    health = self.current_health()
                except Exception:  # pragma: no cover - defensive logging
                    logging.exception("Failed to compute analytics health")
                    health = AnalyticsHealth(generated_at=None, is_fresh=False)
                if not health.is_fresh:
                    if not self._stale_reported:
                        logging.warning(
                            "Analytics snapshot is stale or missing; latest generated_at=%s",
                            (
                                health.generated_at.isoformat().replace("+00:00", "Z")
                                if health.generated_at
                                else "none"
                            ),
                        )
                        self._stale_reported = True
                else:
                    self._stale_reported = False
                interval = max(self._check_interval.total_seconds(), 0.05)
                await asyncio.sleep(interval)
        except asyncio.CancelledError:
            raise

    def _latest_snapshot_timestamp(self) -> Optional[datetime]:
        directory = self._artifact_dir
        if not directory.exists():
            return None

        candidates = sorted(directory.glob("*.json"))
        latest: Optional[datetime] = None
        for path in candidates:
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError):
                continue
            generated_at = payload.get("generated_at") if isinstance(payload, dict) else None
            if not isinstance(generated_at, str):
                continue
            timestamp = _parse_timestamp(generated_at)
            if timestamp and (latest is None or timestamp > latest):
                latest = timestamp
        return latest


__all__ = ["AnalyticsService", "AnalyticsHealth"]
