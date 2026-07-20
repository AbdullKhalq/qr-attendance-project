"""A small persistent blockchain ledger for lectures and attendance records."""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from models import AttendanceRecord, Lecture, utc_now_iso


@dataclass
class Block:
    index: int
    timestamp: str
    record_type: str
    data: dict[str, Any]
    previous_hash: str
    hash: str = ""

    def calculate_hash(self) -> str:
        payload = {
            "index": self.index,
            "timestamp": self.timestamp,
            "record_type": self.record_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def seal(self) -> None:
        self.hash = self.calculate_hash()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Block":
        return cls(**data)


class AttendanceBlockchain:
    """Stores immutable lecture and attendance events in a JSON-backed chain."""

    LECTURE_CREATED = "LECTURE_CREATED"
    ATTENDANCE_RECORDED = "ATTENDANCE_RECORDED"

    def __init__(self, storage_path: str | Path) -> None:
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.chain: list[Block] = []
        self._load_or_create()

    def _genesis_block(self) -> Block:
        block = Block(
            index=0,
            timestamp=utc_now_iso(),
            record_type="GENESIS",
            data={"message": "Automated attendance blockchain initialized"},
            previous_hash="0",
        )
        block.seal()
        return block

    def _load_or_create(self) -> None:
        if not self.storage_path.exists():
            self.chain = [self._genesis_block()]
            self.save()
            return

        try:
            raw = json.loads(self.storage_path.read_text(encoding="utf-8"))
            self.chain = [Block.from_dict(item) for item in raw]
        except (json.JSONDecodeError, OSError, TypeError, KeyError) as exc:
            raise RuntimeError(f"Could not load blockchain: {exc}") from exc

        if not self.chain or not self.is_chain_valid():
            raise RuntimeError("Stored blockchain is missing or invalid.")

    def save(self) -> None:
        with self._lock:
            temp_path = self.storage_path.with_suffix(self.storage_path.suffix + ".tmp")
            content = json.dumps(
                [block.to_dict() for block in self.chain],
                indent=2,
                ensure_ascii=False,
            )
            temp_path.write_text(content, encoding="utf-8")
            temp_path.replace(self.storage_path)

    def _append_block(self, record_type: str, data: dict[str, Any]) -> Block:
        with self._lock:
            previous = self.chain[-1]
            block = Block(
                index=len(self.chain),
                timestamp=utc_now_iso(),
                record_type=record_type,
                data=data,
                previous_hash=previous.hash,
            )
            block.seal()
            self.chain.append(block)
            self.save()
            return block

    def create_lecture(self, lecture: Lecture, qr_token_hash: str) -> Block:
        payload = lecture.to_dict()
        payload["qr_token_hash"] = qr_token_hash
        return self._append_block(self.LECTURE_CREATED, payload)

    def record_attendance(self, record: AttendanceRecord) -> Block:
        return self._append_block(self.ATTENDANCE_RECORDED, record.to_dict())

    def is_chain_valid(self) -> bool:
        if not self.chain:
            return False

        for index, block in enumerate(self.chain):
            if block.index != index or block.hash != block.calculate_hash():
                return False
            if index == 0:
                if block.previous_hash != "0":
                    return False
            elif block.previous_hash != self.chain[index - 1].hash:
                return False
        return True

    def get_lecture(self, lecture_id: str) -> Lecture | None:
        for block in reversed(self.chain):
            if (
                block.record_type == self.LECTURE_CREATED
                and block.data.get("lecture_id") == lecture_id
            ):
                data = {key: value for key, value in block.data.items() if key != "qr_token_hash"}
                return Lecture.from_dict(data)
        return None

    def get_lecture_token_hash(self, lecture_id: str) -> str | None:
        for block in reversed(self.chain):
            if (
                block.record_type == self.LECTURE_CREATED
                and block.data.get("lecture_id") == lecture_id
            ):
                return str(block.data.get("qr_token_hash", "")) or None
        return None

    def list_lectures(self) -> list[Lecture]:
        lectures: list[Lecture] = []
        for block in self.chain:
            if block.record_type == self.LECTURE_CREATED:
                data = {key: value for key, value in block.data.items() if key != "qr_token_hash"}
                lectures.append(Lecture.from_dict(data))
        return list(reversed(lectures))

    def has_attended(self, lecture_id: str, student_id: str) -> bool:
        return any(
            block.record_type == self.ATTENDANCE_RECORDED
            and block.data.get("lecture_id") == lecture_id
            and block.data.get("student_id") == student_id
            for block in self.chain
        )

    def get_attendance_for_lecture(self, lecture_id: str) -> list[AttendanceRecord]:
        return [
            AttendanceRecord.from_dict(block.data)
            for block in self.chain
            if block.record_type == self.ATTENDANCE_RECORDED
            and block.data.get("lecture_id") == lecture_id
        ]

    def get_attendance_for_student(self, student_id: str) -> list[AttendanceRecord]:
        return [
            AttendanceRecord.from_dict(block.data)
            for block in reversed(self.chain)
            if block.record_type == self.ATTENDANCE_RECORDED
            and block.data.get("student_id") == student_id
        ]
