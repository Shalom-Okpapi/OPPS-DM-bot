"""Shared time formatting so replies show West Africa Time consistently."""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

LAGOS_TZ = ZoneInfo("Africa/Lagos")  # UTC+1 year-round, no DST


def now_wat() -> str:
    return datetime.now(timezone.utc).astimezone(LAGOS_TZ).strftime("%-I:%M %p WAT")
