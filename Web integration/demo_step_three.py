"""Console smoke test for Step 3 without starting Flask."""

from pathlib import Path

from attendance_blockchain import AttendanceBlockchain
from config import default_public_base_url
from qr_service import QRService
from repositories import QRTokenRepository, StudentRepository
from services import AttendanceError, AttendanceSystem


def build_demo_system(demo_root: Path) -> AttendanceSystem:
    return AttendanceSystem(
        blockchain=AttendanceBlockchain(demo_root / "attendance_chain.json"),
        students=StudentRepository(demo_root / "students.json"),
        tokens=QRTokenRepository(demo_root / "qr_tokens.json"),
        qr_service=QRService(
            secret_key="step-three-demo-secret",
            public_base_url=default_public_base_url(),
        ),
    )


def main() -> None:
    demo_root = Path(__file__).resolve().parent / "demo_data"
    demo_root.mkdir(parents=True, exist_ok=True)
    system = build_demo_system(demo_root)

    student = system.register_student("2026001", "Demo Student")
    launch = system.create_lecture("CS401", "Distributed Systems", "Dr. Demo", 15)

    qr_file = demo_root / f"{launch.lecture.lecture_id}.png"
    qr_file.write_bytes(system.qr_service.create_qr_png(launch.token))

    print(f"Student: {student.student_id} - {student.name}")
    print(f"Lecture: {launch.lecture.course_code} - {launch.lecture.course_name}")
    print(f"Scan URL: {launch.scan_url}")
    print(f"QR image: {qr_file}")

    record = system.mark_attendance(launch.token, student.student_id)
    print(f"Attendance block record: {record.attendance_id}")
    print(f"Blockchain valid: {system.blockchain.is_chain_valid()}")

    try:
        system.mark_attendance(launch.token, student.student_id)
    except AttendanceError as exc:
        print(f"Duplicate correctly rejected: {exc}")


if __name__ == "__main__":
    main()
