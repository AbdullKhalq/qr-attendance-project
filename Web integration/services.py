"""Application services that coordinate repositories, QR logic, and blockchain writes."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from attendance_blockchain import AttendanceBlockchain
from models import AttendanceRecord, Lecture, Student, utc_now_iso
from qr_service import InvalidQRToken, QRService
from repositories import QRTokenRepository, StudentRepository


class ApplicationError(Exception):
    """Base class for user-facing application errors."""


class ValidationError(ApplicationError):
    pass


class NotFoundError(ApplicationError):
    pass


class AttendanceError(ApplicationError):
    pass


@dataclass(frozen=True)
class LectureLaunch:
    lecture: Lecture
    token: str
    scan_url: str


class AttendanceSystem:
    STUDENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{2,30}$")

    def __init__(
        self,
        blockchain: AttendanceBlockchain,
        students: StudentRepository,
        tokens: QRTokenRepository,
        qr_service: QRService,
    ) -> None:
        self.blockchain = blockchain
        self.students = students
        self.tokens = tokens
        self.qr_service = qr_service

    @staticmethod
    def _required(value: str, label: str, maximum: int = 100) -> str:
        clean = " ".join((value or "").strip().split())
        if not clean:
            raise ValidationError(f"{label} is required.")
        if len(clean) > maximum:
            raise ValidationError(f"{label} must be at most {maximum} characters.")
        return clean

    def register_student(self, student_id: str, name: str) -> Student:
        clean_id = self._required(student_id, "Student ID", 30)
        clean_name = self._required(name, "Student name", 100)
        if not self.STUDENT_ID_PATTERN.fullmatch(clean_id):
            raise ValidationError(
                "Student ID may contain only letters, numbers, underscores, and hyphens."
            )

        existing = self.students.get(clean_id)
        if existing:
            if existing.name.casefold() != clean_name.casefold():
                raise ValidationError("That student ID is already registered to another name.")
            return existing

        return self.students.save(
            Student(student_id=clean_id, name=clean_name, registered_at=utc_now_iso())
        )

    def create_lecture(
        self,
        course_code: str,
        course_name: str,
        lecturer_name: str,
        expires_in_minutes: int,
    ) -> LectureLaunch:
        clean_code = self._required(course_code, "Course code", 30).upper()
        clean_course_name = self._required(course_name, "Course name", 100)
        clean_lecturer = self._required(lecturer_name, "Lecturer name", 100)

        try:
            duration = int(expires_in_minutes)
        except (TypeError, ValueError) as exc:
            raise ValidationError("QR duration must be a whole number.") from exc
        if not 1 <= duration <= 240:
            raise ValidationError("QR duration must be between 1 and 240 minutes.")

        now = datetime.now(timezone.utc)
        lecture = Lecture(
            lecture_id=uuid.uuid4().hex,
            course_code=clean_code,
            course_name=clean_course_name,
            lecturer_name=clean_lecturer,
            created_at=now.isoformat(),
            expires_at=(now + timedelta(minutes=duration)).isoformat(),
        )
        token = self.qr_service.create_token(lecture)
        self.blockchain.create_lecture(lecture, self.qr_service.token_hash(token))
        self.tokens.save(lecture.lecture_id, token)
        return LectureLaunch(lecture, token, self.qr_service.build_scan_url(token))

    def get_lecture(self, lecture_id: str) -> Lecture:
        lecture = self.blockchain.get_lecture(lecture_id)
        if not lecture:
            raise NotFoundError("Lecture not found.")
        return lecture

    def list_lectures(self) -> list[Lecture]:
        return self.blockchain.list_lectures()

    def get_saved_token(self, lecture_id: str) -> str:
        token = self.tokens.get(lecture_id)
        if not token:
            raise NotFoundError("The QR token for this lecture is unavailable.")
        return token

    def inspect_qr(self, token: str) -> Lecture:
        try:
            payload = self.qr_service.validate_token(token)
        except InvalidQRToken as exc:
            raise AttendanceError(str(exc)) from exc

        lecture = self.get_lecture(payload.lecture_id)
        expected_hash = self.blockchain.get_lecture_token_hash(lecture.lecture_id)
        if not expected_hash or expected_hash != self.qr_service.token_hash(token):
            raise AttendanceError("This QR token does not match the blockchain record.")
        if lecture.expires_at != payload.expires_at:
            raise AttendanceError("The QR token does not match the lecture expiry time.")
        return lecture

    def mark_attendance(self, token: str, student_id: str) -> AttendanceRecord:
        lecture = self.inspect_qr(token)
        student = self.students.get(student_id)
        if not student:
            raise AttendanceError("Register as a student before marking attendance.")
        if self.blockchain.has_attended(lecture.lecture_id, student.student_id):
            raise AttendanceError("Attendance has already been recorded for this lecture.")

        record = AttendanceRecord(
            attendance_id=uuid.uuid4().hex,
            lecture_id=lecture.lecture_id,
            student_id=student.student_id,
            student_name=student.name,
            attended_at=utc_now_iso(),
        )
        self.blockchain.record_attendance(record)
        return record

    def lecture_attendance(self, lecture_id: str) -> list[AttendanceRecord]:
        self.get_lecture(lecture_id)
        return self.blockchain.get_attendance_for_lecture(lecture_id)

    def student_attendance(self, student_id: str) -> list[tuple[AttendanceRecord, Lecture]]:
        student = self.students.get(student_id)
        if not student:
            raise NotFoundError("Student not found.")

        result: list[tuple[AttendanceRecord, Lecture]] = []
        for record in self.blockchain.get_attendance_for_student(student_id):
            lecture = self.blockchain.get_lecture(record.lecture_id)
            if lecture:
                result.append((record, lecture))
        return result
