from __future__ import annotations

import json
import tempfile
from pathlib import Path

from app import create_app
from config import Config


class DemoConfig(Config):
    TESTING = True
    SECRET_KEY = "step-two-test-secret"
    LECTURER_REGISTRATION_CODE = "LECTURER-DEMO"



def main() -> None:
    with tempfile.TemporaryDirectory() as temporary_directory:
        DemoConfig.USER_DATA_FILE = Path(temporary_directory) / "users.json"
        app = create_app(DemoConfig)
        client = app.test_client()

        student_response = client.post(
            "/register",
            data={
                "role": "student",
                "full_name": "Sara Ahmed",
                "institutional_id": "S1001",
                "password": "student123",
            },
            follow_redirects=True,
        )
        assert student_response.status_code == 200
        assert b"Student dashboard" in student_response.data

        client.post("/logout")

        lecturer_response = client.post(
            "/register",
            data={
                "role": "lecturer",
                "full_name": "Dr. Omar Ali",
                "institutional_id": "L2001",
                "password": "lecturer123",
                "registration_code": "LECTURER-DEMO",
            },
            follow_redirects=True,
        )
        assert lecturer_response.status_code == 200
        assert b"Lecturer dashboard" in lecturer_response.data
        assert b"S1001" in lecturer_response.data

        client.post("/logout")
        login_response = client.post(
            "/login",
            data={"institutional_id": "S1001", "password": "student123"},
            follow_redirects=True,
        )
        assert login_response.status_code == 200
        assert b"Sara Ahmed" in login_response.data

        stored_users = json.loads(
            DemoConfig.USER_DATA_FILE.read_text(encoding="utf-8")
        )
        assert len(stored_users) == 2
        assert stored_users[0]["password_hash"] != "student123"

        print("Step 2 demo passed.")
        print("- Student registration works")
        print("- Lecturer registration code works")
        print("- Login and sessions work")
        print("- Role-based dashboards work")
        print("- Passwords are stored as hashes")


if __name__ == "__main__":
    main()
