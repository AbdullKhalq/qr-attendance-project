"""Domain models for the attendance application."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any


def utc_now_iso() -> str:
    """Return a timezone-aware UTC timestamp in ISO-8601 format."""
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO-8601 timestamp and require timezone information."""
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("Timestamp must include timezone information.")
    return parsed


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    registered_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Student":
        return cls(**data)


@dataclass(frozen=True)
class Lecture:
    lecture_id: str
    course_code: str
    course_name: str
    lecturer_name: str
    created_at: str
    expires_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Lecture":
        return cls(**data)

    def is_active(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current <= parse_iso(self.expires_at)


@dataclass(frozen=True)
class AttendanceRecord:
    attendance_id: str
    lecture_id: str
    student_id: str
    student_name: str
    attended_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttendanceRecord":
        return cls(**data)
