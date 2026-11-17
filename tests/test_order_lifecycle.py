"""Order lifecycle tests from placement to collection."""
import json
from app.services.order_service import OrderService, OrderStatus, PaymentMethod, PaymentStatus
from app.models.user import User
from app.models.menu import MenuItem
from app.extensions import db
from tests.conftest import login_as


def test_order_placement_and_lifecycle(app, seed_users, seed_menu):
    """Test full order lifecycle: Placed -> Accepted -> Preparing -> Ready -> Collected."""
    with app.app_context():
        student = seed_users["student"]
        item1 = seed_menu["item1"]  # Samosa, price 20, stock 5
        item2 = seed_menu["item2"]  # Chai, price 15, stock 10

        items_payload = [
            {"item_id": item1.id, "quantity": 2},
            {"item_id": item2.id, "quantity": 1},
        ]
        slot = "12:00 PM - 12:30 PM"

        # Place order with Wallet payment
        order = OrderService.place_order(
            user_id=student.id,
            items=items_payload,
            pickup_slot=slot,
            payment_method=PaymentMethod.WALLET
        )

        assert order.id is not None
        assert order.status == OrderStatus.PLACED
        assert order.total_amount == 55.0  # 2*20 + 1*15
        assert order.payment_status == PaymentStatus.PAID

        updated_student = db.session.get(User, student.id)
        assert updated_student.wallet_balance == 145.0  # 200 - 55

        # Check stock decrement
        updated_item1 = db.session.get(MenuItem, item1.id)
        updated_item2 = db.session.get(MenuItem, item2.id)
        assert updated_item1.stock == 3  # 5 - 2
        assert updated_item2.stock == 9  # 10 - 1

        # Staff accepts order
        OrderService.update_order_status(order.id, OrderStatus.ACCEPTED)
        assert order.status == OrderStatus.ACCEPTED

        # Kitchen begins preparing
        OrderService.update_order_status(order.id, OrderStatus.PREPARING)
        assert order.status == OrderStatus.PREPARING

        # Mark ready for pickup
        OrderService.update_order_status(order.id, OrderStatus.READY)
        assert order.status == OrderStatus.READY

        # Mark collected
        OrderService.update_order_status(order.id, OrderStatus.COLLECTED)
        assert order.status == OrderStatus.COLLECTED


def test_payment_methods(app, seed_users, seed_menu):
    """Test UPI and Cash on Pickup payment workflows."""
    with app.app_context():
        student = seed_users["student"]
        item = seed_menu["item2"]  # Chai 15

        # UPI payment
        ord_upi = OrderService.place_order(
            user_id=student.id,
            items=[{"item_id": item.id, "quantity": 1}],
            pickup_slot="12:30 PM - 01:00 PM",
            payment_method=PaymentMethod.UPI
        )
        assert ord_upi.payment_status == PaymentStatus.PAID

        # Cash on pickup payment
        ord_cash = OrderService.place_order(
            user_id=student.id,
            items=[{"item_id": item.id, "quantity": 1}],
            pickup_slot="01:00 PM - 01:30 PM",
            payment_method=PaymentMethod.CASH
        )
        assert ord_cash.payment_status == PaymentStatus.PENDING

        # When cash order is collected, status becomes Paid
        OrderService.update_order_status(ord_cash.id, OrderStatus.COLLECTED)
        assert ord_cash.payment_status == PaymentStatus.PAID


def test_web_checkout_and_status(client, seed_users, seed_menu):
    """Test web checkout view and order status page with live polling."""
    login_as(client, seed_users["student"])

    cart_items = [
        {"item_id": seed_menu["item1"].id, "quantity": 1, "price": 20.0, "name": "Hot Samosa"}
    ]

    res = client.post("/checkout", data={
        "cart_data": json.dumps(cart_items),
        "pickup_slot": "12:00 PM - 12:30 PM",
        "payment_method": "Wallet",
        "idempotency_key": "test_token_123"
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b"placed successfully" in res.data
    assert b"Live updates active" in res.data

    # Live API polling test
    order_id = 1
    api_status_res = client.get(f"/api/orders/{order_id}/status")
    assert api_status_res.status_code == 200
    status_data = api_status_res.get_json()
    assert status_data["id"] == order_id
    assert status_data["status"] == "Placed"
