"""Authentication and role-based access control tests."""
import pytest
from app.services.auth_service import AuthService, AuthenticationError
from tests.conftest import login_as


def test_user_registration_success(app):
    """Test standard user registration."""
    with app.app_context():
        user = AuthService.register_user("john_doe", "john@college.edu", "securePass123", role="student")
        assert user.id is not None
        assert user.username == "john_doe"
        assert user.email == "john@college.edu"
        assert user.role == "student"
        assert user.check_password("securePass123") is True
        assert user.check_password("wrongPassword") is False


def test_user_registration_validation(app):
    """Test duplicate registration and weak password checks."""
    with app.app_context():
        AuthService.register_user("alice", "alice@college.edu", "password123")

        # Duplicate username
        with pytest.raises(ValueError, match="already taken"):
            AuthService.register_user("alice", "alice2@college.edu", "password123")

        # Duplicate email
        with pytest.raises(ValueError, match="already registered"):
            AuthService.register_user("alice_new", "alice@college.edu", "password123")

        # Short password
        with pytest.raises(ValueError, match="at least 6 characters"):
            AuthService.register_user("bob", "bob@college.edu", "123")


def test_user_authentication(app, seed_users):
    """Test user login authentication."""
    with app.app_context():
        # Valid login with username
        user = AuthService.authenticate_user("teststudent", "StudentPass123")
        assert user.username == "teststudent"

        # Valid login with email
        user_by_email = AuthService.authenticate_user("student@test.edu", "StudentPass123")
        assert user_by_email.id == user.id

        # Invalid password
        with pytest.raises(AuthenticationError):
            AuthService.authenticate_user("teststudent", "WrongPass")

        # Nonexistent user
        with pytest.raises(AuthenticationError):
            AuthService.authenticate_user("ghost_user", "AnyPass")


def test_web_auth_flow(client):
    """Test register and login routes via HTTP POST."""
    # Register student via web form
    res = client.post("/auth/register", data={
        "username": "webstudent",
        "email": "webstudent@college.edu",
        "password": "WebPassword123"
    }, follow_redirects=True)
    assert res.status_code == 200
    assert b"Account created successfully" in res.data

    # Login
    login_res = client.post("/auth/login", data={
        "identifier": "webstudent",
        "password": "WebPassword123"
    }, follow_redirects=True)
    assert login_res.status_code == 200
    assert b"Welcome back, webstudent" in login_res.data

    # Logout
    logout_res = client.get("/auth/logout", follow_redirects=True)
    assert logout_res.status_code == 200
    assert b"logged out successfully" in logout_res.data


def test_rbac_access_restrictions(client, seed_users):
    """Test role-based access control protecting staff and admin views."""
    # 1. Unauthenticated request to staff dashboard redirects to login
    res = client.get("/staff/dashboard", follow_redirects=False)
    assert res.status_code == 302
    assert "/auth/login" in res.headers["Location"]

    # 2. Student logged in cannot access staff dashboard (redirected to menu)
    login_as(client, seed_users["student"])
    res = client.get("/staff/dashboard", follow_redirects=True)
    assert res.status_code == 200
    assert b"You do not have permission to access this resource" in res.data

    # 3. Student logged in cannot access admin dashboard
    res = client.get("/admin/dashboard", follow_redirects=True)
    assert res.status_code == 200
    assert b"You do not have permission to access this resource" in res.data

    # 4. Staff logged in can access staff dashboard, but NOT admin dashboard
    login_as(client, seed_users["staff"])
    res_staff = client.get("/staff/dashboard")
    assert res_staff.status_code == 200
    assert b"Live Kitchen Dashboard" in res_staff.data

    res_staff_to_admin = client.get("/admin/dashboard", follow_redirects=True)
    assert b"You do not have permission" in res_staff_to_admin.data

    # 5. Admin can access admin dashboard
    login_as(client, seed_users["admin"])
    res_admin = client.get("/admin/dashboard")
    assert res_admin.status_code == 200
    assert b"Sales &amp; Operations Analytics" in res_admin.data or b"Sales & Operations Analytics" in res_admin.data
