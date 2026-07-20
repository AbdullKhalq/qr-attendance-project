from pathlib import Path
import tempfile
import unittest

from app import ApplicationFactory
from config import ProjectConfig


class WebFlowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        config = ProjectConfig(
            base_dir=Path(__file__).resolve().parents[1],
            data_dir=root,
            blockchain_file=root / "chain.json",
            students_file=root / "students.json",
            qr_tokens_file=root / "tokens.json",
            secret_key="web-test-secret",
            public_base_url="http://localhost",
        )
        self.app = ApplicationFactory.create_app(config)
        self.app.config.update(TESTING=True)
        self.client = self.app.test_client()
        self.system = self.app.extensions["attendance_system"]

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_student_can_register_scan_and_attend(self) -> None:
        launch = self.system.create_lecture("CS450", "Web Systems", "Dr. Test", 15)

        response = self.client.post(
            "/student/register",
            data={"student_id": "S450", "name": "Web Student", "token": launch.token},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Confirm attendance", response.data)

        response = self.client.post(
            "/student/attend",
            data={"token": launch.token},
            follow_redirects=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Attendance recorded on the blockchain", response.data)
        self.assertTrue(
            self.system.blockchain.has_attended(launch.lecture.lecture_id, "S450")
        )

    def test_lecturer_dashboard_loads(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Lecturer dashboard", response.data)


if __name__ == "__main__":
    unittest.main()
