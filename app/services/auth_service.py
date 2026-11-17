"""Authentication service and access control decorators."""
from functools import wraps
from flask import session, redirect, url_for, flash, request, jsonify
from app.extensions import db
from app.models.user import User


class AuthenticationError(Exception):
    pass


class AuthService:
    @staticmethod
    def register_user(username: str, email: str, password: str, role: str = "student",
                      wallet_balance: float = 500.0) -> User:
        """Register a new user with hashed password."""
        username = username.strip()
        email = email.strip().lower()

        if not username or not email or not password:
            raise ValueError("Username, email, and password are required.")

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        if User.query.filter_by(username=username).first():
            raise ValueError(f"Username '{username}' is already taken.")

        if User.query.filter_by(email=email).first():
            raise ValueError(f"Email '{email}' is already registered.")

        if role not in ["student", "staff", "admin"]:
            role = "student"

        user = User(
            username=username,
            email=email,
            role=role,
            wallet_balance=max(0.0, float(wallet_balance)),
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        return user

    @staticmethod
    def authenticate_user(identifier: str, password: str) -> User:
        """Authenticate user by username or email."""
        identifier = identifier.strip()
        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if not user or not user.check_password(password):
            raise AuthenticationError("Invalid username/email or password.")

        return user

    @staticmethod
    def get_user_by_id(user_id: int) -> User:
        """Fetch user by primary key."""
        return db.session.get(User, user_id)


def login_required(f):
    """Decorator to require login for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            if request.path.startswith("/api/"):
                return jsonify({"error": "Unauthorized. Please log in."}), 401
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login", next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def roles_accepted(*roles):
    """Decorator to restrict access to specific user roles."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if "user_id" not in session:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Unauthorized."}), 401
                flash("Please log in first.", "warning")
                return redirect(url_for("auth.login"))

            user_role = session.get("role")
            if user_role not in roles:
                if request.path.startswith("/api/"):
                    return jsonify({"error": "Forbidden. Insufficient permissions."}), 403
                flash("You do not have permission to access this resource.", "danger")
                return redirect(url_for("student.menu_view"))
            return f(*args, **kwargs)
        return decorated_function
    return decorator
