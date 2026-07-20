from __future__ import annotations

import json
import os
import threading
from abc import ABC, abstractmethod
from pathlib import Path

from domain.users import Role, User, user_from_dict


class UserRepository(ABC):
    """Persistence interface used by the service layer."""

    @abstractmethod
    def add(self, user: User) -> None:
        raise NotImplementedError

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def find_by_institutional_id(self, institutional_id: str) -> User | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_role(self, role: Role) -> list[User]:
        raise NotImplementedError


class JsonUserRepository(UserRepository):
    """Small JSON repository suitable for the overnight MVP."""

    def __init__(self, file_path: str | Path) -> None:
        self._file_path = Path(file_path)
        self._lock = threading.RLock()
        self._ensure_file_exists()

    def _ensure_file_exists(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text("[]\n", encoding="utf-8")

    def _load_all(self) -> list[User]:
        try:
            raw = json.loads(self._file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                f"User data file is invalid JSON: {self._file_path}"
            ) from exc

        if not isinstance(raw, list):
            raise RuntimeError("User data file must contain a JSON list.")
        return [user_from_dict(item) for item in raw]

    def _save_all(self, users: list[User]) -> None:
        payload = [user.to_dict() for user in users]
        temp_path = self._file_path.with_suffix(self._file_path.suffix + ".tmp")
        temp_path.write_text(
            json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        os.replace(temp_path, self._file_path)

    def add(self, user: User) -> None:
        with self._lock:
            users = self._load_all()
            if any(existing.user_id == user.user_id for existing in users):
                raise ValueError("A user with this internal ID already exists.")
            users.append(user)
            self._save_all(users)

    def find_by_user_id(self, user_id: str) -> User | None:
        with self._lock:
            return next(
                (user for user in self._load_all() if user.user_id == user_id),
                None,
            )

    def find_by_institutional_id(self, institutional_id: str) -> User | None:
        normalized = institutional_id.strip().casefold()
        with self._lock:
            for user in self._load_all():
                if user.display_identifier.strip().casefold() == normalized:
                    return user
        return None

    def list_by_role(self, role: Role) -> list[User]:
        with self._lock:
            return [user for user in self._load_all() if user.role is role]
