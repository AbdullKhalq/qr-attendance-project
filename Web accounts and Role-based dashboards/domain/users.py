from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any


class Role(str, Enum):
    STUDENT = "student"
    LECTURER = "lecturer"


@dataclass(slots=True)
class User(ABC):
    """Base class shared by every account type."""

    user_id: str
    full_name: str
    password_hash: str
    role: Role

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["role"] = self.role.value
        return data

    @property
    @abstractmethod
    def display_identifier(self) -> str:
        """Human-readable institutional identifier."""


@dataclass(slots=True)
class Student(User):
    student_id: str

    @property
    def display_identifier(self) -> str:
        return self.student_id


@dataclass(slots=True)
class Lecturer(User):
    staff_id: str

    @property
    def display_identifier(self) -> str:
        return self.staff_id


def user_from_dict(data: dict[str, Any]) -> User:
    """Rebuild the correct subclass from JSON repository data."""

    role = Role(data["role"])
    common = {
        "user_id": data["user_id"],
        "full_name": data["full_name"],
        "password_hash": data["password_hash"],
        "role": role,
    }

    if role is Role.STUDENT:
        return Student(student_id=data["student_id"], **common)
    if role is Role.LECTURER:
        return Lecturer(staff_id=data["staff_id"], **common)

    raise ValueError(f"Unsupported role: {role}")
