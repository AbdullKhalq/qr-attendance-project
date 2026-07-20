from __future__ import annotations

import uuid

from werkzeug.security import check_password_hash, generate_password_hash

from domain.users import Lecturer, Role, Student, User
from repositories.user_repository import UserRepository


class RegistrationError(ValueError):
    pass


class AuthenticationError(ValueError):
    pass


class AuthService:
    """Contains registration and authentication business rules."""

    def __init__(
        self,
        repository: UserRepository,
        lecturer_registration_code: str,
    ) -> None:
        self._repository = repository
        self._lecturer_registration_code = lecturer_registration_code

    def register_student(
        self,
        full_name: str,
        student_id: str,
        password: str,
    ) -> Student:
        self._validate_common_fields(full_name, student_id, password)
        self._ensure_identifier_available(student_id)

        student = Student(
            user_id=uuid.uuid4().hex,
            full_name=full_name.strip(),
            password_hash=generate_password_hash(password),
            role=Role.STUDENT,
            student_id=student_id.strip(),
        )
        self._repository.add(student)
        return student

    def register_lecturer(
        self,
        full_name: str,
        staff_id: str,
        password: str,
        registration_code: str,
    ) -> Lecturer:
        self._validate_common_fields(full_name, staff_id, password)
        if registration_code != self._lecturer_registration_code:
            raise RegistrationError("The lecturer registration code is incorrect.")
        self._ensure_identifier_available(staff_id)

        lecturer = Lecturer(
            user_id=uuid.uuid4().hex,
            full_name=full_name.strip(),
            password_hash=generate_password_hash(password),
            role=Role.LECTURER,
            staff_id=staff_id.strip(),
        )
        self._repository.add(lecturer)
        return lecturer

    def authenticate(self, institutional_id: str, password: str) -> User:
        user = self._repository.find_by_institutional_id(institutional_id)
        if user is None or not check_password_hash(user.password_hash, password):
            raise AuthenticationError("Invalid ID or password.")
        return user

    def get_user(self, user_id: str) -> User | None:
        return self._repository.find_by_user_id(user_id)

    @staticmethod
    def _validate_common_fields(
        full_name: str,
        institutional_id: str,
        password: str,
    ) -> None:
        if len(full_name.strip()) < 2:
            raise RegistrationError("Full name must contain at least 2 characters.")
        if len(institutional_id.strip()) < 2:
            raise RegistrationError("Student/staff ID must contain at least 2 characters.")
        if len(password) < 6:
            raise RegistrationError("Password must contain at least 6 characters.")

    def _ensure_identifier_available(self, institutional_id: str) -> None:
        if self._repository.find_by_institutional_id(institutional_id) is not None:
            raise RegistrationError("This student/staff ID is already registered.")
