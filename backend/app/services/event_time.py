from datetime import datetime, timezone

from app.models import EventContent


def event_is_finished(content: EventContent, now: datetime | None = None) -> bool:
    if not content.ends_at:
        return False
    now = now or datetime.now(timezone.utc)
    ends = content.ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    return now >= ends


def seconds_left(content: EventContent, now: datetime | None = None) -> int | None:
    if not content.ends_at:
        return None
    now = now or datetime.now(timezone.utc)
    ends = content.ends_at
    if ends.tzinfo is None:
        ends = ends.replace(tzinfo=timezone.utc)
    return max(0, int((ends - now).total_seconds()))
