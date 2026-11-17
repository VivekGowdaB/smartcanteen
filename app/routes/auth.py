"""Authentication routes (login, register, logout)."""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import AuthService, AuthenticationError

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Register a new student account."""
    if "user_id" in session:
        return redirect(url_for("student.menu_view"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "").strip()
        role = request.form.get("role", "student")

        # Restrict self-registration of staff/admin from public page
        if role not in ["student"]:
            role = "student"

        try:
            user = AuthService.register_user(username, email, password, role=role)
            flash(f"Account created successfully for {user.username}! Please log in.", "success")
            return redirect(url_for("auth.login"))
        except ValueError as e:
            flash(str(e), "danger")

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Authenticate and create user session."""
    if "user_id" in session:
        role = session.get("role")
        if role == "staff":
            return redirect(url_for("staff.dashboard"))
        elif role == "admin":
            return redirect(url_for("admin.dashboard"))
        return redirect(url_for("student.menu_view"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "").strip()

        try:
            user = AuthService.authenticate_user(identifier, password)
            session.clear()
            session["user_id"] = user.id
            session["username"] = user.username
            session["role"] = user.role

            flash(f"Welcome back, {user.username}!", "success")

            next_url = request.args.get("next")
            if next_url and next_url.startswith("/"):
                return redirect(next_url)

            if user.role == "staff":
                return redirect(url_for("staff.dashboard"))
            elif user.role == "admin":
                return redirect(url_for("admin.dashboard"))
            return redirect(url_for("student.menu_view"))

        except AuthenticationError as e:
            flash(str(e), "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Clear session."""
    session.clear()
    flash("You have been logged out successfully.", "info")
    return redirect(url_for("auth.login"))
