"""Tests for system edge cases, concurrency/race conditions, and validation boundaries."""
import pytest
from app.services.order_service import (
    OrderService,
    OrderError,
    OutOfStockError,
    InvalidSlotError,
    DuplicateOrderError,
    InsufficientFundsError,
    CancellationNotAllowedError,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.models.user import User
from app.models.menu import MenuItem
from app.extensions import db


def test_edge_empty_cart(app, seed_users):
    """Edge Case 1: Empty cart submission must be rejected."""
    with app.app_context():
        student = seed_users["student"]
        with pytest.raises(OrderError, match="Cart is empty"):
            OrderService.place_order(student.id, [], "12:00 PM - 12:30 PM")


def test_edge_out_of_stock_race_condition(app, seed_users, seed_menu):
    """
    Edge Case 2: Out-of-stock race condition.
    If an item has 5 portions, and request asks for 6, transaction must fail atomically
    and roll back with OutOfStockError, preserving existing stock and wallet.
    """
    with app.app_context():
        student = seed_users["student"]
        initial_balance = student.wallet_balance
        item1 = seed_menu["item1"]  # initial stock = 5
        initial_stock = item1.stock

        with pytest.raises(OutOfStockError, match="Only 5 portion"):
            OrderService.place_order(
                student.id,
                [{"item_id": item1.id, "quantity": 6}],
                "12:00 PM - 12:30 PM",
                payment_method=PaymentMethod.WALLET
            )

        # Confirm rollback: stock unchanged, wallet untouched
        refreshed_item = seed_menu["item1"]
        refreshed_user = seed_users["student"]
        assert refreshed_item.stock == initial_stock
        assert refreshed_user.wallet_balance == initial_balance

        # Also test ordering an explicitly sold-out item (stock 0)
        item_out = seed_menu["item_out"]
        with pytest.raises(OutOfStockError, match="out of stock"):
            OrderService.place_order(
                student.id,
                [{"item_id": item_out.id, "quantity": 1}],
                "12:00 PM - 12:30 PM"
            )


def test_edge_invalid_or_full_slot(app, seed_users, seed_menu):
    """
    Edge Case 3: Slot limits.
    Configured max_orders per slot is 2 in conftest.
    Placing 2 orders succeeds; placing a 3rd order in the same slot raises InvalidSlotError.
    """
    with app.app_context():
        student = seed_users["student"]
        item = seed_menu["item2"]  # Chai
        slot = "12:00 PM - 12:30 PM"

        # 1st order
        OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 1}], slot)
        # 2nd order
        OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 1}], slot)

        # 3rd order should exceed capacity
        with pytest.raises(InvalidSlotError, match="fully booked"):
            OrderService.place_order(student.id, [{"item_id": item.id, "quantity": 1}], slot)


def test_edge_duplicate_order_submission(app, seed_users, seed_menu):
    """
    Edge Case 4: Duplicate submit with same idempotency key must be rejected.
    """
    with app.app_context():
        student = seed_users["student"]
        item = seed_menu["item1"]
        key = "idemp_token_unique_99"

        # First submit succeeds
        ord1 = OrderService.place_order(
            student.id,
            [{"item_id": item.id, "quantity": 1}],
            "12:30 PM - 01:00 PM",
            idempotency_key=key
        )
        assert ord1.id is not None

        # Second rapid submit with same token fails
        with pytest.raises(DuplicateOrderError):
            OrderService.place_order(
                student.id,
                [{"item_id": item.id, "quantity": 1}],
                "12:30 PM - 01:00 PM",
                idempotency_key=key
            )


def test_edge_cancellation_rules_and_refund(app, seed_users, seed_menu):
    """
    Edge Case 5:
    - Order cancellation is permitted when 'Placed' or 'Accepted'.
    - Restores stock and refunds wallet.
    - Cancellation is strictly forbidden once 'Preparing', 'Ready', or 'Collected'.
    """
    with app.app_context():
        student = seed_users["student"]
        item = seed_menu["item1"]  # Samosa, 20
        starting_stock = item.stock
        starting_balance = student.wallet_balance

        # 1. Place order with wallet
        order = OrderService.place_order(
            student.id,
            [{"item_id": item.id, "quantity": 2}],
            "01:00 PM - 01:30 PM",
            payment_method=PaymentMethod.WALLET
        )
        assert db.session.get(MenuItem, item.id).stock == starting_stock - 2
        assert db.session.get(User, student.id).wallet_balance == starting_balance - 40.0

        # 2. Cancel while in 'Placed' stage -> should succeed and refund
        cancelled_order = OrderService.cancel_order(order.id, user_id=student.id)
        assert cancelled_order.status == OrderStatus.CANCELLED
        assert cancelled_order.payment_status == PaymentStatus.REFUNDED
        assert db.session.get(MenuItem, item.id).stock == starting_stock  # stock restored
        assert db.session.get(User, student.id).wallet_balance == starting_balance  # refunded

        # 3. Create another order and advance to 'Preparing'
        order2 = OrderService.place_order(
            student.id,
            [{"item_id": item.id, "quantity": 1}],
            "01:30 PM - 02:00 PM"
        )
        OrderService.update_order_status(order2.id, OrderStatus.PREPARING)

        # 4. Attempting cancellation after 'Preparing' must raise CancellationNotAllowedError
        with pytest.raises(CancellationNotAllowedError, match="already 'Preparing'"):
            OrderService.cancel_order(order2.id, user_id=student.id)


def test_edge_insufficient_wallet_balance(app, seed_users, seed_menu):
    """
    Edge Case 6: Attempting to pay with wallet when balance is insufficient.
    """
    with app.app_context():
        student = seed_users["student"]
        student.wallet_balance = 10.0  # Set low balance
        db.session.commit()

        item = seed_menu["item1"]  # Samosa = 20.0

        with pytest.raises(InsufficientFundsError, match="Insufficient wallet balance"):
            OrderService.place_order(
                student.id,
                [{"item_id": item.id, "quantity": 1}],
                "05:00 PM - 05:30 PM",
                payment_method=PaymentMethod.WALLET
            )


def test_edge_unauthorized_cancellation(app, seed_users, seed_menu):
    """
    Edge Case 7: A student cannot cancel an order placed by another student.
    """
    with app.app_context():
        student1 = seed_users["student"]
        other_student = User(username="other", email="other@test.edu", role="student", wallet_balance=100.0)
        other_student.set_password("pass123")
        db.session.add(other_student)
        db.session.commit()

        item = seed_menu["item1"]
        order = OrderService.place_order(student1.id, [{"item_id": item.id, "quantity": 1}], "05:00 PM - 05:30 PM")

        with pytest.raises(OrderError, match="Unauthorized"):
            OrderService.cancel_order(order.id, user_id=other_student.id)
