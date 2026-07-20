"""
demo_step_one.py

Run this file to test the AttendanceBlockchain class:

    python demo_step_one.py
"""

import json
from pathlib import Path

from attendance_blockchain import (
    AttendanceBlockchain,
    DuplicateAttendanceError,
)


def main() -> None:
    demo_storage = Path("demo_attendance_chain.json")
    if demo_storage.exists():
        demo_storage.unlink()

    blockchain = AttendanceBlockchain(demo_storage)

    lecture = blockchain.create_lecture(
        course_code="CS401",
        lecturer_id="L001",
        lecture_title="Blockchain Fundamentals",
        expires_in_minutes=15,
    )

    print("QR payload:")
    print(lecture["qr_payload"])

    blockchain.record_attendance(
        lecture_id=lecture["lecture_id"],
        student_id="S1001",
        student_name="Student One",
        qr_token=lecture["qr_token"],
    )

    print("\nStudent attendance:")
    print(
        json.dumps(
            blockchain.get_student_attendance("S1001"),
            indent=2,
        )
    )

    print("\nLecture attendance:")
    print(
        json.dumps(
            blockchain.get_lecture_attendance(lecture["lecture_id"]),
            indent=2,
        )
    )

    print("\nBlockchain valid:", blockchain.is_valid())

    try:
        blockchain.record_attendance(
            lecture_id=lecture["lecture_id"],
            student_id="S1001",
            student_name="Student One",
            qr_token=lecture["qr_token"],
        )
    except DuplicateAttendanceError as exc:
        print("Duplicate prevented:", exc)


if __name__ == "__main__":
    main()
