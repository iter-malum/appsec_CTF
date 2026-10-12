from collections import defaultdict, deque
from threading import Lock
from time import time

from fastapi import HTTPException, Request


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, key: str, limit: int, window_sec: int) -> None:
        now = time()
        with self._lock:
            q = self._hits[key]
            while q and q[0] <= now - window_sec:
                q.popleft()
            if len(q) >= limit:
                raise HTTPException(
                    status_code=429,
                    detail="Слишком много попыток. Подождите минуту.",
                )
            q.append(now)


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    # Next.js rewrite / reverse proxy may pass the real client.
    # API is not meant to be exposed publicly; still sanitize length.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64] or "unknown"
    if request.client and request.client.host:
        return request.client.host
    return "unknown"
