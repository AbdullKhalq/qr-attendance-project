"""Step 3 entry point: Flask web application factory."""

from __future__ import annotations

from flask import Flask

from attendance_blockchain import AttendanceBlockchain
from config import ProjectConfig
from controllers import LecturerController, StudentController
from qr_service import QRService
from repositories import QRTokenRepository, StudentRepository
from services import AttendanceSystem


class ApplicationFactory:
    @staticmethod
    def build_system(config: ProjectConfig) -> AttendanceSystem:
        blockchain = AttendanceBlockchain(config.blockchain_file)
        students = StudentRepository(config.students_file)
        tokens = QRTokenRepository(config.qr_tokens_file)
        qr_service = QRService(config.secret_key, config.public_base_url)
        return AttendanceSystem(blockchain, students, tokens, qr_service)

    @classmethod
    def create_app(cls, config: ProjectConfig | None = None) -> Flask:
        project_config = config or ProjectConfig.from_environment()
        app = Flask(__name__)
        app.config.update(
            SECRET_KEY=project_config.secret_key,
            TEMPLATES_AUTO_RELOAD=True,
        )

        system = cls.build_system(project_config)
        app.extensions["attendance_system"] = system
        app.register_blueprint(LecturerController(system).blueprint)
        app.register_blueprint(StudentController(system).blueprint)
        return app


app = ApplicationFactory.create_app()


if __name__ == "__main__":
    system = app.extensions["attendance_system"]
    print(f"QR attendance URL: {system.qr_service.public_base_url}")
    app.run(host="0.0.0.0", port=5000, debug=True)
