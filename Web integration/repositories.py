"""JSON repositories for mutable data that should not be placed on the chain."""

from __future__ import annotations

import json
import threading
from pathlib import Path
from typing import Any

from models import Student


class AtomicJsonStore:
    def __init__(self, path: str | Path, default: dict[str, Any] | None = None) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.default = default or {}
        self._lock = threading.RLock()
        if not self.path.exists():
            self.write(dict(self.default))

    def read(self) -> dict[str, Any]:
        with self._lock:
            try:
                return json.loads(self.path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError) as exc:
                raise RuntimeError(f"Could not read {self.path.name}: {exc}") from exc

    def write(self, data: dict[str, Any]) -> None:
        with self._lock:
            temp_path = self.path.with_suffix(self.path.suffix + ".tmp")
            temp_path.write_text(
                json.dumps(data, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            temp_path.replace(self.path)


class StudentRepository:
    def __init__(self, path: str | Path) -> None:
        self.store = AtomicJsonStore(path)

    def save(self, student: Student) -> Student:
        data = self.store.read()
        data[student.student_id] = student.to_dict()
        self.store.write(data)
        return student

    def get(self, student_id: str) -> Student | None:
        raw = self.store.read().get(student_id)
        return Student.from_dict(raw) if raw else None

    def list_all(self) -> list[Student]:
        return [Student.from_dict(item) for item in self.store.read().values()]


class QRTokenRepository:
    """Keeps QR tokens so lecturers can reopen and display an existing QR."""

    def __init__(self, path: str | Path) -> None:
        self.store = AtomicJsonStore(path)

    def save(self, lecture_id: str, token: str) -> None:
        data = self.store.read()
        data[lecture_id] = token
        self.store.write(data)

    def get(self, lecture_id: str) -> str | None:
        token = self.store.read().get(lecture_id)
        return str(token) if token else None
