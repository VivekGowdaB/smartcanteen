"""Pytest fixtures and test configuration."""
import pytest
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.menu import Category, MenuItem
from app.models.order import PickupSlotConfig
from app.services.order_service import DEFAULT_SLOTS


@pytest.fixture
def app():
    """Create test application configured for testing."""
    test_app = create_app("testing")
    with test_app.app_context():
        db.create_all()
        # Seed default slots
        for slot in DEFAULT_SLOTS:
            db.session.add(PickupSlotConfig(slot_time=slot, max_orders=2, is_active=True))
        db.session.commit()
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Test client."""
    return app.test_client()


@pytest.fixture
def seed_users(app):
    """Create standard student, staff, and admin users."""
    student = User(username="teststudent", email="student@test.edu", role="student", wallet_balance=200.0)
    student.set_password("StudentPass123")

    staff = User(username="teststaff", email="staff@test.edu", role="staff", wallet_balance=50.0)
    staff.set_password("StaffPass123")

    admin = User(username="testadmin", email="admin@test.edu", role="admin", wallet_balance=50.0)
    admin.set_password("AdminPass123")

    db.session.add_all([student, staff, admin])
    db.session.commit()

    return {"student": student, "staff": staff, "admin": admin}


@pytest.fixture
def seed_menu(app):
    """Create sample categories and menu items."""
    cat = Category(name="Snacks", description="Delicious snacks")
    db.session.add(cat)
    db.session.flush()

    item1 = MenuItem(
        category_id=cat.id,
        name="Hot Samosa",
        description="Spicy potato filled snack",
        price=20.0,
        stock=5,
        is_available=True,
        prep_time_minutes=5
    )
    item2 = MenuItem(
        category_id=cat.id,
        name="Masala Chai",
        description="Hot cardamom tea",
        price=15.0,
        stock=10,
        is_available=True,
        prep_time_minutes=3
    )
    item_out = MenuItem(
        category_id=cat.id,
        name="Sold Out Roll",
        description="Currently unavailable",
        price=40.0,
        stock=0,
        is_available=False,
        prep_time_minutes=5
    )

    db.session.add_all([item1, item2, item_out])
    db.session.commit()

    return {"category": cat, "item1": item1, "item2": item2, "item_out": item_out}


def login_as(client, user):
    """Helper to simulate session login."""
    with client.session_transaction() as sess:
        sess["user_id"] = user.id
        sess["username"] = user.username
        sess["role"] = user.role
