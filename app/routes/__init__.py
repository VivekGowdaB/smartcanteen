"""Routes package exports."""
from app.routes.auth import auth_bp
from app.routes.student import student_bp
from app.routes.staff import staff_bp
from app.routes.admin import admin_bp
from app.routes.api import api_bp

__all__ = ["auth_bp", "student_bp", "staff_bp", "admin_bp", "api_bp"]
