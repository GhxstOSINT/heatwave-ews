"""Small process-local abuse controls and request-size enforcement.

The deployment should also use an edge/WAF limit: in-memory limits reset on
restart and are not shared between multiple application instances.
"""

from __future__ import annotations

import json
import threading
import time
from collections import defaultdict, deque
from collections.abc import Awaitable, Callable
from typing import Any


class SlidingWindowLimiter:
    """Bound requests by route and caller key over a rolling time window."""

    def __init__(self, *, max_keys: int = 20_000) -> None:
        self._events: dict[tuple[str, str], deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._max_keys = max_keys

    def allow(self, route: str, key: str, limit: int, window: int, now: float | None = None) -> tuple[bool, int]:
        current = time.monotonic() if now is None else now
        cutoff = current - window
        bucket_key = (route, key)
        with self._lock:
            if bucket_key not in self._events and len(self._events) >= self._max_keys:
                self._prune_all(cutoff)
                if len(self._events) >= self._max_keys:
                    return False, window
            events = self._events[bucket_key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                return False, max(1, int(events[0] + window - current + 0.999))
            events.append(current)
            return True, 0

    def _prune_all(self, cutoff: float) -> None:
        for bucket_key in list(self._events):
            events = self._events[bucket_key]
            while events and events[0] <= cutoff:
                events.popleft()
            if not events:
                del self._events[bucket_key]

    def clear(self) -> None:
        """Reset stored windows (used by deterministic tests)."""
        with self._lock:
            self._events.clear()


class RequestBodyLimitMiddleware:
    """Reject oversized mutation bodies before framework JSON parsing."""

    def __init__(self, app: Callable[..., Awaitable[None]], default_limit: int = 1_048_576) -> None:
        self.app = app
        self.default_limit = default_limit

    async def __call__(self, scope: dict[str, Any], receive: Callable[..., Awaitable[dict[str, Any]]], send: Callable[..., Awaitable[None]]) -> None:
        if scope.get("type") != "http" or scope.get("method") not in {"POST", "PUT", "PATCH", "DELETE"}:
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        limit = 15_000_000 if path == "/forecast-upload" else 16_000_000 if path == "/health-data/import" else self.default_limit
        headers = {key.lower(): value for key, value in scope.get("headers", [])}
        raw_length = headers.get(b"content-length")
        if raw_length:
            try:
                if int(raw_length) > limit:
                    await self._too_large(scope, receive, send)
                    return
            except ValueError:
                await self._too_large(scope, receive, send)
                return

        buffered: list[dict[str, Any]] = []
        total = 0
        while True:
            message = await receive()
            buffered.append(message)
            if message.get("type") == "http.request":
                total += len(message.get("body", b""))
                if total > limit:
                    await self._too_large(scope, receive, send)
                    return
                if not message.get("more_body", False):
                    break
            elif message.get("type") == "http.disconnect":
                break

        async def replay_receive() -> dict[str, Any]:
            if buffered:
                return buffered.pop(0)
            return await receive()

        await self.app(scope, replay_receive, send)

    @staticmethod
    async def _too_large(scope: dict[str, Any], receive: Callable[..., Awaitable[dict[str, Any]]], send: Callable[..., Awaitable[None]]) -> None:
        body = json.dumps({"detail": "Request body is too large"}).encode()
        await send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode()), (b"cache-control", b"no-store")]})
        await send({"type": "http.response.body", "body": body})
