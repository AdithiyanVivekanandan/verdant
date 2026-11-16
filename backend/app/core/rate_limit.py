"""Simple in-memory fixed-window rate limiter middleware.

Tracks requests per client IP and returns HTTP 429 when the configured
requests-per-window limit is exceeded. No external dependencies; suitable for
single-instance development deployments. Production deployments behind a proxy
should rely on edge/CDN rate limiting and key on `X-Forwarded-For` instead of
the direct client host.
"""
import time
from collections import defaultdict
from threading import Lock

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class RateLimitMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        *,
        limit: int = 60,
        window_seconds: int = 60,
        path_limits: dict[str, tuple[int, int]] | None = None,
    ) -> None:
        self.app = app
        self.limit = limit
        self.window_seconds = window_seconds
        # Per-path overrides: path -> (limit, window_seconds)
        self.path_limits = path_limits or {}
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._lock = Lock()

    def _client_key(self, request: Request) -> str:
        # Direct client host; note that behind a reverse proxy this should be
        # derived from X-Forwarded-For after validating the proxy.
        client = request.client
        return client.host if client else "unknown"

    def _limits_for_path(self, path: str) -> tuple[int, int]:
        return self.path_limits.get(path, (self.limit, self.window_seconds))

    def _allowed(self, key: str, limit: int, window: int) -> bool:
        now = time.time()
        with self._lock:
            window_start = now - window
            # Prune timestamps outside the current window.
            self._buckets[key] = [t for t in self._buckets[key] if t > window_start]
            if len(self._buckets[key]) >= limit:
                return False
            self._buckets[key].append(now)
            return True

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        path = request.url.path
        limit, window = self._limits_for_path(path)
        key = f"{self._client_key(request)}:{path}"

        if not self._allowed(key, limit, window):
            response = JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again later."},
                headers={"Retry-After": str(window)},
            )
            await response(scope, receive, send)
            return

        await self.app(scope, receive, send)
