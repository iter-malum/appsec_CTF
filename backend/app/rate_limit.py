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
                    detail="Слишком много попыток. Подождите минуту и попробуйте снова.",
                )
            q.append(now)


limiter = RateLimiter()


def client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
