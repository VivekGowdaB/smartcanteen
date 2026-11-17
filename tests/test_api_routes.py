"""API route tests covering JSON endpoints and error responses."""
from app.services.order_service import OrderService
from tests.conftest import login_as


def test_api_slots_endpoint(client):
    """Test GET /api/slots returns slot list."""
    res = client.get("/api/slots")
    assert res.status_code == 200
    slots = res.get_json()
    assert isinstance(slots, list)
    assert len(slots) > 0
    assert "slot_time" in slots[0]
    assert "is_full" in slots[0]


def test_api_create_order_flow(client, seed_users, seed_menu):
    """Test POST /api/orders JSON creation, validation, and cancel."""
    login_as(client, seed_users["student"])
    item = seed_menu["item1"]

    # 1. Missing items
    res_empty = client.post("/api/orders", json={"items": [], "pickup_slot": "12:00 PM - 12:30 PM"})
    assert res_empty.status_code == 400

    # 2. Missing slot
    res_noslot = client.post("/api/orders", json={"items": [{"item_id": item.id, "quantity": 1}]})
    assert res_noslot.status_code == 400

    # 3. Successful JSON order
    res_order = client.post("/api/orders", json={
        "items": [{"item_id": item.id, "quantity": 1}],
        "pickup_slot": "12:00 PM - 12:30 PM",
        "payment_method": "Cash on Pickup"
    })
    assert res_order.status_code == 201
    order_data = res_order.get_json()["order"]
    order_id = order_data["id"]
    assert order_data["status"] == "Placed"

    # 4. JSON order status poll
    res_poll = client.get(f"/api/orders/{order_id}/status")
    assert res_poll.status_code == 200
    assert res_poll.get_json()["id"] == order_id

    # 5. Cancel via API
    res_cancel = client.post(f"/api/orders/{order_id}/cancel")
    assert res_cancel.status_code == 200
    assert res_cancel.get_json()["order"]["status"] == "Cancelled"


def test_api_staff_status_update(client, seed_users, seed_menu):
    """Test staff programmatic status update via POST /api/staff/orders/<id>/status."""
    student = seed_users["student"]
    item = seed_menu["item1"]
    order = OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 1}], "05:00 PM - 05:30 PM")

    login_as(client, seed_users["staff"])
    res = client.post(f"/api/staff/orders/{order.id}/status", json={"status": "Accepted"})
    assert res.status_code == 200
    assert res.get_json()["order"]["status"] == "Accepted"


def test_student_web_views(client, seed_users, seed_menu):
    """Test student history, cart, and cancel web views."""
    login_as(client, seed_users["student"])

    # View cart
    res_cart = client.get("/cart")
    assert res_cart.status_code == 200
    assert b"Your Cart" in res_cart.data

    # View history
    res_hist = client.get("/history")
    assert res_hist.status_code == 200
    assert b"My Order History" in res_hist.data

    # Place order and cancel via web route
    item = seed_menu["item1"]
    order = OrderService.place_order(
        seed_users["student"].id,
        [{"item_id": item.id, "quantity": 1}],
        "05:30 PM - 06:00 PM"
    )
    cancel_res = client.post(f"/orders/{order.id}/cancel", follow_redirects=True)
    assert cancel_res.status_code == 200
    assert b"has been cancelled" in cancel_res.data
