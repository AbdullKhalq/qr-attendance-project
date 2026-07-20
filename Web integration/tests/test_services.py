from pathlib import Path
import tempfile
import unittest

from attendance_blockchain import AttendanceBlockchain
from qr_service import QRService
from repositories import QRTokenRepository, StudentRepository
from services import AttendanceError, AttendanceSystem


class AttendanceSystemTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.system = AttendanceSystem(
            AttendanceBlockchain(root / "chain.json"),
            StudentRepository(root / "students.json"),
            QRTokenRepository(root / "tokens.json"),
            QRService("test-secret", "http://localhost:5000"),
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_full_attendance_flow(self) -> None:
        student = self.system.register_student("S100", "Sara Student")
        launch = self.system.create_lecture("CS401", "Blockchain", "Dr. Ali", 15)
        record = self.system.mark_attendance(launch.token, student.student_id)

        self.assertEqual(record.lecture_id, launch.lecture.lecture_id)
        self.assertTrue(self.system.blockchain.is_chain_valid())
        self.assertEqual(len(self.system.student_attendance(student.student_id)), 1)

    def test_duplicate_attendance_is_rejected(self) -> None:
        student = self.system.register_student("S200", "Omar Student")
        launch = self.system.create_lecture("CS402", "Networks", "Dr. Noor", 15)
        self.system.mark_attendance(launch.token, student.student_id)

        with self.assertRaises(AttendanceError):
            self.system.mark_attendance(launch.token, student.student_id)


if __name__ == "__main__":
    unittest.main()
