"""Flask controllers. Route definitions stay separate from business logic."""

from __future__ import annotations

from flask import (
    Blueprint,
    Response,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from services import ApplicationError, AttendanceSystem


class LecturerController:
    def __init__(self, system: AttendanceSystem) -> None:
        self.system = system
        self.blueprint = Blueprint("lecturer", __name__)
        self._register_routes()

    def _register_routes(self) -> None:
        self.blueprint.add_url_rule("/", view_func=self.dashboard, methods=["GET"])
        self.blueprint.add_url_rule(
            "/lecturer/lectures", view_func=self.create_lecture, methods=["POST"]
        )
        self.blueprint.add_url_rule(
            "/lecturer/lectures/<lecture_id>", view_func=self.lecture_details, methods=["GET"]
        )
        self.blueprint.add_url_rule(
            "/lecturer/lectures/<lecture_id>/qr.png", view_func=self.qr_png, methods=["GET"]
        )

    def dashboard(self):
        lectures = []
        for lecture in self.system.list_lectures():
            lectures.append(
                {
                    "lecture": lecture,
                    "active": lecture.is_active(),
                    "attendance_count": len(
                        self.system.blockchain.get_attendance_for_lecture(lecture.lecture_id)
                    ),
                }
            )
        return render_template(
            "lecturer_dashboard.html",
            lectures=lectures,
            chain_valid=self.system.blockchain.is_chain_valid(),
        )

    def create_lecture(self):
        try:
            launch = self.system.create_lecture(
                course_code=request.form.get("course_code", ""),
                course_name=request.form.get("course_name", ""),
                lecturer_name=request.form.get("lecturer_name", ""),
                expires_in_minutes=request.form.get("expires_in_minutes", "15"),
            )
            flash("Lecture and QR code created.", "success")
            return redirect(
                url_for("lecturer.lecture_details", lecture_id=launch.lecture.lecture_id)
            )
        except ApplicationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("lecturer.dashboard"))

    def lecture_details(self, lecture_id: str):
        try:
            lecture = self.system.get_lecture(lecture_id)
            token = self.system.get_saved_token(lecture_id)
            records = self.system.lecture_attendance(lecture_id)
            return render_template(
                "lecture_details.html",
                lecture=lecture,
                token=token,
                scan_url=self.system.qr_service.build_scan_url(token),
                records=records,
                active=lecture.is_active(),
            )
        except ApplicationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("lecturer.dashboard"))

    def qr_png(self, lecture_id: str):
        try:
            token = self.system.get_saved_token(lecture_id)
            return Response(self.system.qr_service.create_qr_png(token), mimetype="image/png")
        except ApplicationError as exc:
            return Response(str(exc), status=404, mimetype="text/plain")


class StudentController:
    def __init__(self, system: AttendanceSystem) -> None:
        self.system = system
        self.blueprint = Blueprint("student", __name__)
        self._register_routes()

    def _register_routes(self) -> None:
        self.blueprint.add_url_rule(
            "/student/register", view_func=self.register, methods=["GET", "POST"]
        )
        self.blueprint.add_url_rule(
            "/student/scan", view_func=self.scan, methods=["GET"]
        )
        self.blueprint.add_url_rule(
            "/student/attend", view_func=self.attend, methods=["POST"]
        )
        self.blueprint.add_url_rule(
            "/student/attendance", view_func=self.attendance, methods=["GET"]
        )
        self.blueprint.add_url_rule(
            "/student/logout", view_func=self.logout, methods=["POST"]
        )

    def register(self):
        token = request.values.get("token", "")
        if request.method == "GET":
            return render_template("student_register.html", token=token)

        try:
            student = self.system.register_student(
                request.form.get("student_id", ""), request.form.get("name", "")
            )
            session["student_id"] = student.student_id
            flash(f"Registered as {student.name}.", "success")
            if token:
                return redirect(url_for("student.scan", token=token))
            return redirect(url_for("student.attendance"))
        except ApplicationError as exc:
            flash(str(exc), "error")
            return render_template("student_register.html", token=token), 400

    def scan(self):
        token = request.args.get("token", "")
        if not token:
            return render_template(
                "message.html",
                title="Missing QR token",
                message="Open this page by scanning a lecture QR code.",
            ), 400

        student_id = session.get("student_id")
        if not student_id:
            return redirect(url_for("student.register", token=token))

        try:
            lecture = self.system.inspect_qr(token)
            student = self.system.students.get(student_id)
            already_attended = self.system.blockchain.has_attended(
                lecture.lecture_id, student_id
            )
            return render_template(
                "student_scan.html",
                lecture=lecture,
                student=student,
                token=token,
                already_attended=already_attended,
            )
        except ApplicationError as exc:
            return render_template(
                "message.html", title="QR code rejected", message=str(exc)
            ), 400

    def attend(self):
        token = request.form.get("token", "")
        student_id = session.get("student_id")
        if not student_id:
            return redirect(url_for("student.register", token=token))

        try:
            self.system.mark_attendance(token, student_id)
            flash("Attendance recorded on the blockchain.", "success")
            return redirect(url_for("student.attendance"))
        except ApplicationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("student.scan", token=token))

    def attendance(self):
        student_id = session.get("student_id")
        if not student_id:
            return redirect(url_for("student.register"))

        try:
            student = self.system.students.get(student_id)
            rows = self.system.student_attendance(student_id)
            return render_template("student_attendance.html", student=student, rows=rows)
        except ApplicationError as exc:
            flash(str(exc), "error")
            return redirect(url_for("student.register"))

    def logout(self):
        session.clear()
        return redirect(url_for("student.register"))
