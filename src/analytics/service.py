"""Background worker integrating analytics generation with health reporting."""

from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter

from .cli import DEFAULT_ARTIFACT_DIR
from .scheduler import AnalyticsRefreshScheduler

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _HealthStatus:
    """Internal representation of the analytics freshness state."""

    latest_generated_at: Optional[str]
    is_fresh: bool
    checked_at: datetime


class AnalyticsService:
    """Wrap :class:`AnalyticsRefreshScheduler` with health monitoring."""

    def __init__(
        self,
        *,
        scheduler: Optional[AnalyticsRefreshScheduler] = None,
        artifact_dir: Path | str = DEFAULT_ARTIFACT_DIR,
        freshness_window: timedelta = timedelta(minutes=10),
        check_interval: float = 60.0,
    ) -> None:
        self._artifact_dir = Path(artifact_dir)
        self._freshness_window = freshness_window
        self._check_interval = check_interval
        self._scheduler = scheduler or AnalyticsRefreshScheduler(artifact_dir=self._artifact_dir)

        self._health_lock = asyncio.Lock()
        self._monitor_task: Optional[asyncio.Task[None]] = None
        self._latest_status: Optional[_HealthStatus] = None
        self._alert_emitted = False

        router = APIRouter(prefix="/analytics", tags=["analytics"])

        @router.get("/health")
        async def _health_endpoint() -> dict[str, object]:
            status = await self.refresh_health()
            return {
                "is_fresh": status.is_fresh,
                "latest_generated_at": status.latest_generated_at,
            }

        self.router = router

    @property
    def scheduler(self) -> AnalyticsRefreshScheduler:
        """Expose the underlying scheduler for integration tests."""

        return self._scheduler

    @property
    def status_hook(self):
        """Callable hook for :class:`reviews.store.ReviewStore`."""

        return self._scheduler.handle_status_change

    async def start(self) -> None:
        """Start the scheduler and background health monitor."""

        await self._scheduler.start()
        await self.refresh_health()
        self._monitor_task = asyncio.create_task(self._monitor_loop())

    async def shutdown(self) -> None:
        """Stop the background monitor and shutdown the scheduler."""

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None
        await self._scheduler.shutdown()

    async def refresh_health(self) -> _HealthStatus:
        """Re-evaluate the freshness of analytics artifacts."""

        async with self._health_lock:
            status = await asyncio.to_thread(self._compute_health_status)
            self._latest_status = status
            if not status.is_fresh:
                if not self._alert_emitted:
                    self._emit_stale_warning(status)
                    self._alert_emitted = True
            else:
                self._alert_emitted = False
            return status

    async def _monitor_loop(self) -> None:
        try:
            while True:
                await self.refresh_health()
                await asyncio.sleep(self._check_interval)
        except asyncio.CancelledError:
            pass

    def _compute_health_status(self) -> _HealthStatus:
        now = datetime.now(timezone.utc)
        latest_generated_at: Optional[str] = None
        latest_timestamp: Optional[datetime] = None

        if self._artifact_dir.exists():
            candidates = sorted(self._artifact_dir.glob("*.json"))
            for candidate in reversed(candidates):
                try:
                    payload = json.loads(candidate.read_text(encoding="utf-8"))
                except (OSError, json.JSONDecodeError):
                    continue
                generated_at = payload.get("generated_at")
                if isinstance(generated_at, str):
                    parsed = self._parse_timestamp(generated_at)
                    if parsed is not None:
                        latest_generated_at = generated_at
                        latest_timestamp = parsed
                        break
                    latest_generated_at = generated_at
        is_fresh = False
        if latest_timestamp is not None:
            delta = now - latest_timestamp
            is_fresh = delta <= self._freshness_window

        return _HealthStatus(
            latest_generated_at=latest_generated_at,
            is_fresh=is_fresh,
            checked_at=now,
        )

    def _emit_stale_warning(self, status: _HealthStatus) -> None:
        if status.latest_generated_at:
            logger.warning(
                "No fresh analytics snapshot found; latest generated at %s", status.latest_generated_at
            )
        else:
            logger.warning(
                "No analytics snapshots available in %s", self._artifact_dir.as_posix()
            )

    @staticmethod
    def _parse_timestamp(timestamp: str) -> Optional[datetime]:
        try:
            formatted = timestamp.replace("Z", "+00:00")
            parsed = datetime.fromisoformat(formatted)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

    def current_health(self) -> Optional[dict[str, object]]:
        """Return the last computed health snapshot without forcing a refresh."""

        status = self._latest_status
        if status is None:
            return None
        return {
            "is_fresh": status.is_fresh,
            "latest_generated_at": status.latest_generated_at,
            "checked_at": status.checked_at.isoformat().replace("+00:00", "Z"),
        }


__all__ = ["AnalyticsService"]
