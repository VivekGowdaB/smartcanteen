"""Staff operations and Admin sales reporting tests."""
import csv
import io
from app.services.order_service import OrderService, OrderStatus
from app.models.menu import MenuItem
from app.extensions import db
from tests.conftest import login_as


def test_staff_dashboard_and_operations(client, seed_users, seed_menu):
    """Test staff viewing queue, transitioning orders, and editing stock."""
    login_as(client, seed_users["staff"])

    # 1. Place order as student first
    student = seed_users["student"]
    item = seed_menu["item1"]
    order = OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 1}], "12:00 PM - 12:30 PM")

    # 2. Staff views dashboard
    res = client.get("/staff/dashboard")
    assert res.status_code == 200
    assert f"Order #{order.id}".encode() in res.data

    # 3. Staff advances status to Accepted
    update_res = client.post(f"/staff/orders/{order.id}/status", data={"status": "Accepted"}, follow_redirects=True)
    assert update_res.status_code == 200
    assert b"transitioned to" in update_res.data and b"Accepted" in update_res.data

    # 4. Staff adjusts stock via form
    stock_res = client.post("/staff/menu", data={
        "action": "update_stock",
        "item_id": item.id,
        "stock": 42
    }, follow_redirects=True)
    assert stock_res.status_code == 200
    assert b"Stock updated" in stock_res.data
    assert db.session.get(MenuItem, item.id).stock == 42

    # 5. Staff toggles availability
    toggle_res = client.post("/staff/menu", data={
        "action": "toggle_availability",
        "item_id": item.id
    }, follow_redirects=True)
    assert toggle_res.status_code == 200
    assert db.session.get(MenuItem, item.id).is_available is False

    # 6. Staff creates a new item
    add_res = client.post("/staff/menu", data={
        "action": "add_item",
        "category_id": seed_menu["category"].id,
        "name": "Paneer Roll",
        "description": "Tasty roll",
        "price": 80.0,
        "stock": 15,
        "prep_time_minutes": 8
    }, follow_redirects=True)
    assert add_res.status_code == 200
    assert b"Added new menu item" in add_res.data


def test_admin_sales_reporting_and_csv(client, seed_users, seed_menu):
    """Test Admin analytics view and CSV export format."""
    # Place a completed order
    student = seed_users["student"]
    item = seed_menu["item1"]
    order = OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 2}], "12:00 PM - 12:30 PM")
    OrderService.update_order_status(order.id, OrderStatus.COLLECTED)

    login_as(client, seed_users["admin"])

    # 1. Admin dashboard
    dash_res = client.get("/admin/dashboard")
    assert dash_res.status_code == 200
    assert b"Sales &amp; Operations Analytics" in dash_res.data or b"Sales & Operations Analytics" in dash_res.data
    assert b"Total Revenue Collected" in dash_res.data

    # 2. CSV export
    csv_res = client.get("/admin/sales/csv")
    assert csv_res.status_code == 200
    assert csv_res.mimetype == "text/csv"
    assert "attachment; filename=" in csv_res.headers.get("Content-Disposition", "")

    csv_text = csv_res.data.decode("utf-8")
    csv_reader = list(csv.reader(io.StringIO(csv_text)))
    assert len(csv_reader) >= 2  # Header + at least 1 order row
    header = csv_reader[0]
    assert "Order ID" in header
    assert "Total Amount (INR)" in header
    assert "Status" in header

    # 3. JSON API sales
    api_sales = client.get("/api/admin/sales")
    assert api_sales.status_code == 200
    sales_data = api_sales.get_json()
    assert sales_data["total_orders"] >= 1
    assert sales_data["total_revenue"] >= 40.0
