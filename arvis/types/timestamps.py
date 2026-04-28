# arvis/types/timestamps.py

from datetime import UTC, datetime


def utcnow() -> datetime:
    return datetime.now(UTC)
