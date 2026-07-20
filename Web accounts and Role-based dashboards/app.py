from __future__ import annotations

from flask import Flask, render_template

from config import Config
from controllers import AuthController, DashboardController
from repositories import JsonUserRepository
from services import AuthService


class AttendanceWebApplication:
    """Composition root that connects repositories, services, and controllers."""

    def __init__(self, config_object: type[Config] = Config) -> None:
        self.flask_app = Flask(__name__)
        self.flask_app.config.from_object(config_object)
        self._configure_dependencies()
        self._register_routes()

    def _configure_dependencies(self) -> None:
        self.user_repository = JsonUserRepository(
            self.flask_app.config["USER_DATA_FILE"]
        )
        self.auth_service = AuthService(
            repository=self.user_repository,
            lecturer_registration_code=self.flask_app.config[
                "LECTURER_REGISTRATION_CODE"
            ],
        )
        self.auth_controller = AuthController(self.auth_service)
        self.dashboard_controller = DashboardController(
            auth_service=self.auth_service,
            user_repository=self.user_repository,
        )

    def _register_routes(self) -> None:
        app = self.flask_app
        app.register_blueprint(self.auth_controller.blueprint)
        app.register_blueprint(self.dashboard_controller.blueprint)

        @app.get("/")
        def home():
            return render_template("index.html")


def create_app(config_object: type[Config] = Config) -> Flask:
    return AttendanceWebApplication(config_object).flask_app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)
