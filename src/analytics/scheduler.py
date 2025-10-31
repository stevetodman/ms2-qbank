"""Async helpers for regenerating analytics artifacts on demand."""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Mapping, Optional

from .cli import (
    DEFAULT_ARTIFACT_DIR,
    DEFAULT_DATA_DIR,
    DEFAULT_DOCS_JSON,
    DEFAULT_DOCS_MARKDOWN,
    run_generation_cycle,
)


GenerationRunner = Callable[[Path, Path, Optional[Path], Optional[Path]], Mapping[str, object]]


class AnalyticsRefreshScheduler:
    """Coordinate background analytics generation with debounce support."""

    def __init__(
        self,
        *,
        data_dir: Path = DEFAULT_DATA_DIR,
        artifact_dir: Path = DEFAULT_ARTIFACT_DIR,
        docs_markdown: Optional[Path] = DEFAULT_DOCS_MARKDOWN,
        docs_json: Optional[Path] = DEFAULT_DOCS_JSON,
        debounce_seconds: float = 5.0,
        runner: Optional[GenerationRunner] = None,
    ) -> None:
        self._data_dir = Path(data_dir)
        self._artifact_dir = Path(artifact_dir)
        self._docs_markdown = Path(docs_markdown) if docs_markdown else None
        self._docs_json = Path(docs_json) if docs_json else None
        self._debounce_seconds = debounce_seconds
        self._runner = runner or run_generation_cycle

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._debounce_handle: Optional[asyncio.TimerHandle] = None
        self._task: Optional[asyncio.Task[Mapping[str, object]]] = None
        self._lock = asyncio.Lock()
        self._last_completed_at: Optional[datetime] = None

    async def start(self) -> None:
        """Bind the scheduler to the currently running asyncio loop."""

        self._loop = asyncio.get_running_loop()

    async def shutdown(self) -> None:
        """Cancel any pending work and release resources."""

        if self._debounce_handle:
            self._debounce_handle.cancel()
            self._debounce_handle = None

        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._task = None

    async def handle_status_change(self, *_: object) -> None:
        """Async hook compatible with :class:`reviews.store.ReviewStore`."""

        self.request_refresh()

    def request_refresh(self) -> None:
        """Schedule a refresh if one is not already pending."""

        loop = self._loop
        if loop is None:
            return

        def _arm_debounce() -> None:
            if self._debounce_handle:
                self._debounce_handle.cancel()
            self._debounce_handle = loop.call_later(
                self._debounce_seconds, self._launch_generation
            )

        loop.call_soon_threadsafe(_arm_debounce)

    def _launch_generation(self) -> None:
        self._debounce_handle = None
        if self._task and not self._task.done():
            return
        self._task = asyncio.create_task(self._run_generation())

    async def _run_generation(self) -> Mapping[str, object]:
        async with self._lock:
            result = await asyncio.to_thread(
                self._runner,
                self._data_dir,
                self._artifact_dir,
                self._docs_markdown,
                self._docs_json,
            )
            generated_at = result.get("generated_at")
            if isinstance(generated_at, str):
                try:
                    timestamp = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            self._last_completed_at = timestamp.astimezone(timezone.utc)
            return result

    @property
    def last_completed_at(self) -> Optional[datetime]:
        """UTC timestamp of the most recent successful generation."""

        return self._last_completed_at


__all__ = ["AnalyticsRefreshScheduler"]

