from __future__ import annotations

from functools import wraps
from typing import Any, Callable, TypeVar, cast

from flask import Blueprint, flash, redirect, render_template, session, url_for

from domain.users import Role, User
from repositories.user_repository import UserRepository
from services.auth_service import AuthService

F = TypeVar("F", bound=Callable[..., Any])


class DashboardController:
    """Role-aware dashboard controller."""

    def __init__(
        self,
        auth_service: AuthService,
        user_repository: UserRepository,
    ) -> None:
        self._auth_service = auth_service
        self._user_repository = user_repository
        self.blueprint = Blueprint("dashboard", __name__)
        self._register_routes()

    def _register_routes(self) -> None:
        protected_dashboard = self._login_required(self.dashboard)
        self.blueprint.add_url_rule(
            "/dashboard", view_func=protected_dashboard, methods=["GET"]
        )

    def _current_user(self) -> User | None:
        user_id = session.get("user_id")
        if not isinstance(user_id, str):
            return None
        return self._auth_service.get_user(user_id)

    def _login_required(self, view_function: F) -> F:
        @wraps(view_function)
        def wrapped(*args: Any, **kwargs: Any):
            if self._current_user() is None:
                session.clear()
                flash("Please log in first.", "error")
                return redirect(url_for("auth.login"))
            return view_function(*args, **kwargs)

        return cast(F, wrapped)

    def dashboard(self):
        user = self._current_user()
        assert user is not None

        if user.role is Role.LECTURER:
            students = self._user_repository.list_by_role(Role.STUDENT)
            return render_template(
                "lecturer_dashboard.html",
                user=user,
                students=students,
            )

        return render_template("student_dashboard.html", user=user)
