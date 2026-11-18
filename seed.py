"""Database seeder script for Smart Canteen Ordering System."""
import argparse
import os
import sys
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.menu import Category, MenuItem
from app.models.order import Order, OrderItem, PickupSlotConfig, OrderStatus, PaymentMethod, PaymentStatus
from app.services.order_service import DEFAULT_SLOTS


def seed_database():
    return _seed_database(reset=True)


def _seed_database(reset):
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        if reset:
            print("[*] Dropping and recreating all database tables...")
            db.drop_all()
        db.create_all()

        print("[*] Seeding pickup slot configurations...")
        for slot in DEFAULT_SLOTS:
            slot_config = PickupSlotConfig(slot_time=slot, max_orders=10, is_active=True)
            db.session.add(slot_config)

        print("[*] Seeding system users...")
        admin = User(username="admin", email="admin@canteen.college.edu", role="admin", wallet_balance=1000.0)
        admin.set_password("Admin@123")

        staff = User(username="staff", email="staff@canteen.college.edu", role="staff", wallet_balance=500.0)
        staff.set_password("Staff@123")

        student1 = User(username="student1", email="student1@student.college.edu", role="student", wallet_balance=500.0)
        student1.set_password("Student@123")

        student2 = User(username="student2", email="student2@student.college.edu", role="student", wallet_balance=350.0)
        student2.set_password("Student@123")

        db.session.add_all([admin, staff, student1, student2])
        db.session.flush()

        print("[*] Seeding categories and menu items...")
        cat_south = Category(name="South Indian", description="Fresh steamed idlis, crispy dosas, and authentic chutneys")
        cat_meals = Category(name="Meals & Bowls", description="Wholesome rice bowls, thalis, and curries")
        cat_snacks = Category(name="Snacks & Quick Bites", description="Hot samosas, sandwiches, and crisp fries")
        cat_beverages = Category(name="Beverages", description="Brewed coffees, fresh teas, and cool milkshakes")

        db.session.add_all([cat_south, cat_meals, cat_snacks, cat_beverages])
        db.session.flush()

        items = [
            MenuItem(category_id=cat_south.id, name="Masala Dosa", description="Golden crispy crepe filled with spiced potato masala", price=60.0, stock=25, prep_time_minutes=8),
            MenuItem(category_id=cat_south.id, name="Idli Vada Combo", description="Two steamed rice cakes with one crispy medu vada and sambar", price=50.0, stock=30, prep_time_minutes=5),
            MenuItem(category_id=cat_south.id, name="Onion Uttapam", description="Thick rice pancake topped with chopped red onions and green chillies", price=65.0, stock=15, prep_time_minutes=10),
            MenuItem(category_id=cat_meals.id, name="Special Veg Thali", description="Paneer curry, dal tadka, 2 rotis, jeera rice, salad and sweet", price=120.0, stock=20, prep_time_minutes=15),
            MenuItem(category_id=cat_meals.id, name="Hyderabadi Veg Biryani", description="Fragrant basmati rice slow-cooked with fresh vegetables and aromatic spices", price=110.0, stock=18, prep_time_minutes=12),
            MenuItem(category_id=cat_meals.id, name="Curd Rice Bowl", description="Cool tempered yogurt rice with mustard seeds, curry leaves and pomegranate", price=55.0, stock=20, prep_time_minutes=4),
            MenuItem(category_id=cat_snacks.id, name="Crispy Samosa (2 pcs)", description="Flaky golden pastry pockets stuffed with spiced potato and peas", price=30.0, stock=40, prep_time_minutes=3),
            MenuItem(category_id=cat_snacks.id, name="Veg Cheese Grilled Sandwich", description="Three-layer toasted sandwich stuffed with crisp vegetables and cheddar", price=75.0, stock=15, prep_time_minutes=7),
            MenuItem(category_id=cat_snacks.id, name="Peri Peri French Fries", description="Hot crispy potato fries dusted with piquant peri peri seasoning", price=60.0, stock=25, prep_time_minutes=6),
            MenuItem(category_id=cat_beverages.id, name="Authentic Filter Coffee", description="Rich South Indian chicory-blend coffee brewed with whole milk", price=25.0, stock=50, prep_time_minutes=3),
            MenuItem(category_id=cat_beverages.id, name="Masala Chai", description="Aromatic spiced Indian tea infused with cardamom, ginger, and cloves", price=20.0, stock=50, prep_time_minutes=3),
            MenuItem(category_id=cat_beverages.id, name="Mango Lassi", description="Chilled, creamy yogurt smoothie churned with sweet Alphonso mango pulp", price=45.0, stock=25, prep_time_minutes=4),
        ]
        db.session.add_all(items)
        db.session.flush()

        print("[*] Seeding initial demo orders...")
        # Order 1: Completed order for analytics
        ord1 = Order(
            user_id=student1.id,
            status=OrderStatus.COLLECTED,
            pickup_slot="12:00 PM - 12:30 PM",
            payment_method=PaymentMethod.WALLET,
            payment_status=PaymentStatus.PAID,
            total_amount=135.0,
            estimated_wait_minutes=11,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(ord1)
        db.session.flush()

        oi1 = OrderItem(order_id=ord1.id, menu_item_id=items[0].id, quantity=1, unit_price=60.0, subtotal=60.0)
        oi2 = OrderItem(order_id=ord1.id, menu_item_id=items[7].id, quantity=1, unit_price=75.0, subtotal=75.0)
        db.session.add_all([oi1, oi2])

        # Order 2: In-progress order for kitchen board
        ord2 = Order(
            user_id=student2.id,
            status=OrderStatus.PREPARING,
            pickup_slot="12:30 PM - 01:00 PM",
            payment_method=PaymentMethod.UPI,
            payment_status=PaymentStatus.PAID,
            total_amount=130.0,
            estimated_wait_minutes=15,
            created_at=datetime.now(timezone.utc)
        )
        db.session.add(ord2)
        db.session.flush()

        oi3 = OrderItem(order_id=ord2.id, menu_item_id=items[4].id, quantity=1, unit_price=110.0, subtotal=110.0)
        oi4 = OrderItem(order_id=ord2.id, menu_item_id=items[10].id, quantity=1, unit_price=20.0, subtotal=20.0)
        db.session.add_all([oi3, oi4])

        db.session.commit()
        print("\n[+] Database seeding complete!")
        print("-------------------------------------------------------")
        print("Demo Credentials:")
        print("  Admin:   admin     / Admin@123")
        print("  Staff:   staff     / Staff@123")
        print("  Student: student1  / Student@123  (Wallet: Rs 500)")
        print("  Student: student2  / Student@123  (Wallet: Rs 350)")
        print("-------------------------------------------------------")


def seed_if_empty():
    app = create_app(os.environ.get("FLASK_ENV", "development"))
    with app.app_context():
        db.create_all()
        models = (User, Category, MenuItem, PickupSlotConfig, Order, OrderItem)
        if any(db.session.query(model).first() for model in models):
            print("[*] Existing database data detected; skipping demo seed.")
            return

    _seed_database(reset=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed the Smart Canteen database.")
    parser.add_argument(
        "--if-empty",
        action="store_true",
        help="Seed demo data only when the database contains no records."
    )
    arguments = parser.parse_args()
    if arguments.if_empty:
        seed_if_empty()
    else:
        seed_database()
