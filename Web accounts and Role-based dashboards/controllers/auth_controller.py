from __future__ import annotations

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from domain.users import Role
from services.auth_service import AuthenticationError, AuthService, RegistrationError


class AuthController:
    """HTTP controller for registration, login, and logout."""

    def __init__(self, auth_service: AuthService) -> None:
        self._auth_service = auth_service
        self.blueprint = Blueprint("auth", __name__)
        self._register_routes()

    def _register_routes(self) -> None:
        self.blueprint.add_url_rule(
            "/register", view_func=self.register, methods=["GET", "POST"]
        )
        self.blueprint.add_url_rule(
            "/login", view_func=self.login, methods=["GET", "POST"]
        )
        self.blueprint.add_url_rule(
            "/logout", view_func=self.logout, methods=["POST"]
        )

    def register(self):
        if request.method == "GET":
            return render_template("register.html", roles=Role)

        role_value = request.form.get("role", "").strip().lower()
        full_name = request.form.get("full_name", "")
        institutional_id = request.form.get("institutional_id", "")
        password = request.form.get("password", "")

        try:
            role = Role(role_value)
            if role is Role.STUDENT:
                user = self._auth_service.register_student(
                    full_name=full_name,
                    student_id=institutional_id,
                    password=password,
                )
            else:
                user = self._auth_service.register_lecturer(
                    full_name=full_name,
                    staff_id=institutional_id,
                    password=password,
                    registration_code=request.form.get("registration_code", ""),
                )
        except (ValueError, RegistrationError) as exc:
            flash(str(exc), "error")
            return render_template("register.html", roles=Role), 400

        session.clear()
        session["user_id"] = user.user_id
        flash("Account created successfully.", "success")
        return redirect(url_for("dashboard.dashboard"))

    def login(self):
        if request.method == "GET":
            return render_template("login.html")

        try:
            user = self._auth_service.authenticate(
                institutional_id=request.form.get("institutional_id", ""),
                password=request.form.get("password", ""),
            )
        except AuthenticationError as exc:
            flash(str(exc), "error")
            return render_template("login.html"), 401

        session.clear()
        session["user_id"] = user.user_id
        flash(f"Welcome, {user.full_name}.", "success")
        return redirect(url_for("dashboard.dashboard"))

    @staticmethod
    def logout():
        session.clear()
        flash("You have been logged out.", "success")
        return redirect(url_for("home"))
