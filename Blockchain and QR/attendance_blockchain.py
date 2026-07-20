"""
attendance_blockchain.py

A small educational blockchain ledger for a QR-code student attendance system.

This is intentionally a simple private blockchain for a university project.
It demonstrates hashing, immutable linked records, validation, persistence,
lecture sessions, QR-token verification, and duplicate-attendance prevention.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
from pathlib import Path
import secrets
from typing import Any
from uuid import uuid4


class BlockchainError(Exception):
    """Base exception for attendance-blockchain errors."""


class LectureNotFoundError(BlockchainError):
    """Raised when a lecture session does not exist."""


class InvalidQRTokenError(BlockchainError):
    """Raised when a QR token is incorrect."""


class LectureExpiredError(BlockchainError):
    """Raised when attendance is attempted after a lecture QR expires."""


class DuplicateAttendanceError(BlockchainError):
    """Raised when a student has already attended the lecture."""


@dataclass
class Block:
    """Represents one block in the attendance blockchain."""

    index: int
    timestamp: str
    record_type: str
    data: dict[str, Any]
    previous_hash: str
    hash: str = ""

    def calculate_hash(self) -> str:
        """Calculate a deterministic SHA-256 hash for this block."""
        block_content = {
            "index": self.index,
            "timestamp": self.timestamp,
            "record_type": self.record_type,
            "data": self.data,
            "previous_hash": self.previous_hash,
        }
        encoded = json.dumps(
            block_content,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def seal(self) -> None:
        """Calculate and store the block hash."""
        self.hash = self.calculate_hash()

    def to_dict(self) -> dict[str, Any]:
        """Convert the block into a JSON-serializable dictionary."""
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Block":
        """Rebuild a Block from saved JSON data."""
        return cls(
            index=int(value["index"]),
            timestamp=str(value["timestamp"]),
            record_type=str(value["record_type"]),
            data=dict(value["data"]),
            previous_hash=str(value["previous_hash"]),
            hash=str(value["hash"]),
        )


class AttendanceBlockchain:
    """
    Manages lecture-session and student-attendance blocks.

    Public workflow:
        1. lecturer calls create_lecture()
        2. returned qr_payload is converted into a QR code
        3. student scans it
        4. the app calls record_attendance()
    """

    def __init__(self, storage_file: str | Path = "attendance_chain.json") -> None:
        self.storage_file = Path(storage_file)
        self.chain: list[Block] = []

        if self.storage_file.exists():
            self.load()
        else:
            self.chain = [self._create_genesis_block()]
            self.save()

    @staticmethod
    def _utc_now() -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def _utc_now_iso(cls) -> str:
        return cls._utc_now().isoformat()

    @staticmethod
    def _hash_qr_token(token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()

    def _create_genesis_block(self) -> Block:
        block = Block(
            index=0,
            timestamp=self._utc_now_iso(),
            record_type="GENESIS",
            data={"message": "Attendance blockchain initialized"},
            previous_hash="0",
        )
        block.seal()
        return block

    def _append_block(self, record_type: str, data: dict[str, Any]) -> Block:
        if not self.is_valid():
            raise BlockchainError(
                "The blockchain is invalid. Refusing to append a new block."
            )

        previous_block = self.chain[-1]
        new_block = Block(
            index=len(self.chain),
            timestamp=self._utc_now_iso(),
            record_type=record_type,
            data=data,
            previous_hash=previous_block.hash,
        )
        new_block.seal()
        self.chain.append(new_block)
        self.save()
        return new_block

    def create_lecture(
        self,
        course_code: str,
        lecturer_id: str,
        lecture_title: str = "",
        expires_in_minutes: int = 15,
    ) -> dict[str, str]:
        """
        Create a lecture session and return data needed to generate its QR code.

        The raw QR token is returned once but is never stored directly on-chain.
        Only its SHA-256 hash is stored.
        """
        course_code = course_code.strip()
        lecturer_id = lecturer_id.strip()
        lecture_title = lecture_title.strip()

        if not course_code:
            raise ValueError("course_code cannot be empty.")
        if not lecturer_id:
            raise ValueError("lecturer_id cannot be empty.")
        if expires_in_minutes <= 0:
            raise ValueError("expires_in_minutes must be greater than zero.")

        lecture_id = str(uuid4())
        qr_token = secrets.token_urlsafe(32)
        created_at = self._utc_now()
        expires_at = created_at + timedelta(minutes=expires_in_minutes)

        self._append_block(
            record_type="LECTURE_CREATED",
            data={
                "lecture_id": lecture_id,
                "course_code": course_code,
                "lecture_title": lecture_title,
                "lecturer_id": lecturer_id,
                "created_at": created_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "qr_token_hash": self._hash_qr_token(qr_token),
            },
        )

        qr_payload = json.dumps(
            {"lecture_id": lecture_id, "token": qr_token},
            separators=(",", ":"),
        )

        return {
            "lecture_id": lecture_id,
            "qr_token": qr_token,
            "qr_payload": qr_payload,
            "expires_at": expires_at.isoformat(),
        }

    def record_attendance(
        self,
        lecture_id: str,
        student_id: str,
        qr_token: str,
        student_name: str = "",
    ) -> Block:
        """Verify the QR token and record one student's attendance."""
        lecture_id = lecture_id.strip()
        student_id = student_id.strip()
        qr_token = qr_token.strip()
        student_name = student_name.strip()

        if not lecture_id:
            raise ValueError("lecture_id cannot be empty.")
        if not student_id:
            raise ValueError("student_id cannot be empty.")
        if not qr_token:
            raise ValueError("qr_token cannot be empty.")

        lecture = self.get_lecture(lecture_id)
        if lecture is None:
            raise LectureNotFoundError(
                f"No lecture was found with ID '{lecture_id}'."
            )

        expected_hash = lecture["qr_token_hash"]
        provided_hash = self._hash_qr_token(qr_token)
        if not hmac.compare_digest(expected_hash, provided_hash):
            raise InvalidQRTokenError("The scanned QR token is invalid.")

        expires_at = datetime.fromisoformat(lecture["expires_at"])
        if self._utc_now() > expires_at:
            raise LectureExpiredError("This lecture QR code has expired.")

        if self.has_attended(lecture_id, student_id):
            raise DuplicateAttendanceError(
                f"Student '{student_id}' has already attended this lecture."
            )

        return self._append_block(
            record_type="ATTENDANCE_RECORDED",
            data={
                "attendance_id": str(uuid4()),
                "lecture_id": lecture_id,
                "course_code": lecture["course_code"],
                "student_id": student_id,
                "student_name": student_name,
                "attended_at": self._utc_now_iso(),
            },
        )

    def get_lecture(self, lecture_id: str) -> dict[str, Any] | None:
        """Return lecture data for a lecture ID, or None."""
        for block in reversed(self.chain):
            if (
                block.record_type == "LECTURE_CREATED"
                and block.data.get("lecture_id") == lecture_id
            ):
                return dict(block.data)
        return None

    def has_attended(self, lecture_id: str, student_id: str) -> bool:
        """Check whether a student already has an attendance block."""
        return any(
            block.record_type == "ATTENDANCE_RECORDED"
            and block.data.get("lecture_id") == lecture_id
            and block.data.get("student_id") == student_id
            for block in self.chain
        )

    def get_student_attendance(self, student_id: str) -> list[dict[str, Any]]:
        """Return all attendance records belonging to one student."""
        return [
            dict(block.data)
            for block in self.chain
            if block.record_type == "ATTENDANCE_RECORDED"
            and block.data.get("student_id") == student_id
        ]

    def get_lecture_attendance(self, lecture_id: str) -> list[dict[str, Any]]:
        """Return all students recorded for one lecture."""
        return [
            dict(block.data)
            for block in self.chain
            if block.record_type == "ATTENDANCE_RECORDED"
            and block.data.get("lecture_id") == lecture_id
        ]

    def is_valid(self) -> bool:
        """Verify every hash and every link in the blockchain."""
        if not self.chain:
            return False

        genesis = self.chain[0]
        if (
            genesis.index != 0
            or genesis.previous_hash != "0"
            or genesis.hash != genesis.calculate_hash()
        ):
            return False

        for index in range(1, len(self.chain)):
            current = self.chain[index]
            previous = self.chain[index - 1]

            if current.index != index:
                return False
            if current.hash != current.calculate_hash():
                return False
            if current.previous_hash != previous.hash:
                return False

        return True

    def save(self) -> None:
        """Save the blockchain to a JSON file."""
        self.storage_file.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "version": 1,
            "chain": [block.to_dict() for block in self.chain],
        }

        try:
            self.storage_file.write_text(
                json.dumps(payload, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
        except PermissionError as exc:
            raise BlockchainError(
                f"Permission denied while saving '{self.storage_file}'. "
                "Close the file if it is open and make sure it is not read-only."
            ) from exc

    def load(self) -> None:
        """Load and validate the blockchain from its JSON file."""
        try:
            payload = json.loads(self.storage_file.read_text(encoding="utf-8"))
            loaded_chain = [
                Block.from_dict(block_data)
                for block_data in payload.get("chain", [])
            ]
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise BlockchainError(
                f"Could not load blockchain file: {self.storage_file}"
            ) from exc

        old_chain = self.chain
        self.chain = loaded_chain

        if not self.is_valid():
            self.chain = old_chain
            raise BlockchainError(
                f"Saved blockchain is invalid or has been modified: "
                f"{self.storage_file}"
            )

    def export_chain(self) -> list[dict[str, Any]]:
        """Return the complete ledger for a lecturer/admin blockchain viewer."""
        return [block.to_dict() for block in self.chain]
