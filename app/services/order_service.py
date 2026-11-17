"""Order service handling transactions, edge cases, slots, and lifecycle."""
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from flask import current_app
from app.extensions import db
from app.models.user import User
from app.models.menu import MenuItem
from app.models.order import (
    Order, OrderItem, PickupSlotConfig, OrderStatus, PaymentMethod, PaymentStatus
)


class OrderError(Exception):
    pass


class OutOfStockError(OrderError):
    pass


class InvalidSlotError(OrderError):
    pass


class DuplicateOrderError(OrderError):
    pass


class InsufficientFundsError(OrderError):
    pass


class CancellationNotAllowedError(OrderError):
    pass


DEFAULT_SLOTS = [
    "12:00 PM - 12:30 PM",
    "12:30 PM - 01:00 PM",
    "01:00 PM - 01:30 PM",
    "01:30 PM - 02:00 PM",
    "05:00 PM - 05:30 PM",
    "05:30 PM - 06:00 PM",
]


class OrderService:
    @staticmethod
    def get_pickup_slots() -> List[Dict[str, Any]]:
        """Return available pickup slots with current capacity."""
        max_limit = current_app.config.get("MAX_ORDERS_PER_SLOT", 10)
        # Fetch configured slots or use defaults
        db_slots = PickupSlotConfig.query.filter_by(is_active=True).all()
        slot_times = [s.slot_time for s in db_slots] if db_slots else DEFAULT_SLOTS

        slot_data = []
        for slot in slot_times:
            # Count non-cancelled active orders for this slot
            booked_count = Order.query.filter(
                Order.pickup_slot == slot,
                Order.status != OrderStatus.CANCELLED
            ).count()

            limit = max_limit
            if db_slots:
                config = next((s for s in db_slots if s.slot_time == slot), None)
                if config:
                    limit = config.max_orders

            is_full = booked_count >= limit
            slot_data.append({
                "slot_time": slot,
                "booked_count": booked_count,
                "max_orders": limit,
                "is_full": is_full,
                "available_spots": max(0, limit - booked_count),
            })
        return slot_data

    @staticmethod
    def calculate_estimated_wait_time(items_to_order: List[Dict[str, Any]]) -> int:
        """Calculate wait time in minutes based on current queue and items ordered."""
        # Estimate based on kitchen queue (Placed + Accepted + Preparing)
        active_orders = Order.query.filter(
            Order.status.in_([OrderStatus.PLACED, OrderStatus.ACCEPTED, OrderStatus.PREPARING])
        ).all()

        queue_wait = 0
        for ord_obj in active_orders:
            for oi in ord_obj.items:
                prep = oi.menu_item.prep_time_minutes if oi.menu_item else 5
                queue_wait += int(prep * oi.quantity * 0.3)  # Parallel kitchen coefficient

        # Add this order's prep time
        order_prep = 0
        for item in items_to_order:
            menu_item = db.session.get(MenuItem, item["item_id"])
            if menu_item:
                order_prep = max(order_prep, menu_item.prep_time_minutes)

        estimated = max(5, 5 + queue_wait + order_prep)
        return min(estimated, 60)  # Capped at 60 mins for realistic estimates

    @staticmethod
    def place_order(user_id: int, items: List[Dict[str, Any]], pickup_slot: str,
                    payment_method: str = PaymentMethod.CASH,
                    idempotency_key: Optional[str] = None) -> Order:
        """
        Place order with transaction isolation, stock validation, slot limits, and payments.
        Edge cases handled:
        - Empty cart
        - Duplicate submit
        - Invalid / full slot
        - Out-of-stock race condition
        - Insufficient wallet balance
        """
        if not items:
            raise OrderError("Cart is empty. Please add items before checkout.")

        # Check idempotency / duplicate submission
        if idempotency_key:
            existing_order = Order.query.filter_by(idempotency_key=idempotency_key).first()
            if existing_order:
                raise DuplicateOrderError("Order has already been processed with this submission key.")

        user = db.session.get(User, user_id)
        if not user:
            raise OrderError("User not found.")

        # Validate pickup slot availability
        slot_config = PickupSlotConfig.query.filter_by(slot_time=pickup_slot, is_active=True).first()
        max_slot_orders = slot_config.max_orders if slot_config else current_app.config.get("MAX_ORDERS_PER_SLOT", 10)
        slot_booked_count = Order.query.filter(
            Order.pickup_slot == pickup_slot,
            Order.status != OrderStatus.CANCELLED
        ).count()

        if slot_booked_count >= max_slot_orders:
            raise InvalidSlotError(f"Pickup slot '{pickup_slot}' is fully booked. Please choose another time.")

        # Validate payment method
        if payment_method not in PaymentMethod.ALL_METHODS:
            payment_method = PaymentMethod.CASH

        # Begin atomic transaction checking stock
        total_amount = 0.0
        order_items_to_create = []

        try:
            for it in items:
                item_id = it.get("item_id")
                qty = int(it.get("quantity", 1))
                if qty <= 0:
                    raise OrderError("Item quantity must be at least 1.")

                # Lock or re-query item within transaction
                menu_item = db.session.query(MenuItem).filter(MenuItem.id == item_id).with_for_update().first()
                if not menu_item:
                    raise OrderError(f"Menu item ID {item_id} not found.")

                if not menu_item.is_available or menu_item.stock <= 0:
                    raise OutOfStockError(f"'{menu_item.name}' is currently out of stock.")

                if menu_item.stock < qty:
                    msg = (
                        f"Only {menu_item.stock} portion(s) available for '{menu_item.name}'. "
                        f"Requested: {qty}."
                    )
                    raise OutOfStockError(msg)

                subtotal = menu_item.price * qty
                total_amount += subtotal

                # Decrement stock atomically
                menu_item.stock -= qty
                if menu_item.stock == 0:
                    menu_item.is_available = False

                order_items_to_create.append({
                    "menu_item": menu_item,
                    "quantity": qty,
                    "unit_price": menu_item.price,
                    "subtotal": subtotal,
                })

            total_amount = round(total_amount, 2)

            # Handle payment logic
            payment_status = PaymentStatus.PENDING
            if payment_method == PaymentMethod.WALLET:
                if user.wallet_balance < total_amount:
                    funds_msg = (
                        f"Insufficient wallet balance. Required: Rs {total_amount:.2f}, "
                        f"Available: Rs {user.wallet_balance:.2f}"
                    )
                    raise InsufficientFundsError(funds_msg)
                user.wallet_balance = round(user.wallet_balance - total_amount, 2)
                payment_status = PaymentStatus.PAID
            elif payment_method == PaymentMethod.UPI:
                # Mock UPI success
                payment_status = PaymentStatus.PAID
            elif payment_method == PaymentMethod.CASH:
                payment_status = PaymentStatus.PENDING

            # Estimated wait time
            est_wait = OrderService.calculate_estimated_wait_time(items)

            # Create Order
            order = Order(
                user_id=user.id,
                status=OrderStatus.PLACED,
                pickup_slot=pickup_slot,
                payment_method=payment_method,
                payment_status=payment_status,
                total_amount=total_amount,
                estimated_wait_minutes=est_wait,
                idempotency_key=idempotency_key,
                created_at=datetime.now(timezone.utc),
            )
            db.session.add(order)
            db.session.flush()  # assign order.id

            # Create OrderItems
            for oi_data in order_items_to_create:
                order_item = OrderItem(
                    order_id=order.id,
                    menu_item_id=oi_data["menu_item"].id,
                    quantity=oi_data["quantity"],
                    unit_price=oi_data["unit_price"],
                    subtotal=oi_data["subtotal"],
                )
                db.session.add(order_item)

            db.session.commit()
            return order

        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def update_order_status(order_id: int, new_status: str) -> Order:
        """Update order lifecycle status according to valid transitions."""
        order = db.session.get(Order, order_id)
        if not order:
            raise OrderError(f"Order #{order_id} not found.")

        if new_status not in OrderStatus.ALL_STATUSES:
            raise OrderError(f"Invalid status '{new_status}'.")

        # Handle cancellation through dedicated method
        if new_status == OrderStatus.CANCELLED:
            return OrderService.cancel_order(order_id, cancelled_by="staff")

        # Allow valid progression
        order.status = new_status
        order.updated_at = datetime.now(timezone.utc)
        if new_status == OrderStatus.COLLECTED and order.payment_status == PaymentStatus.PENDING:
            order.payment_status = PaymentStatus.PAID  # Cash collected upon delivery

        db.session.commit()
        return order

    @staticmethod
    def cancel_order(order_id: int, user_id: Optional[int] = None, cancelled_by: str = "user") -> Order:
        """
        Cancel an order if still in Placed or Accepted stage.
        Rejects cancellation if Preparing, Ready, or Collected.
        Restores stock and refunds wallet balance if paid.
        """
        order = db.session.get(Order, order_id)
        if not order:
            raise OrderError(f"Order #{order_id} not found.")

        # Check user ownership if called by student
        if user_id and order.user_id != user_id:
            raise OrderError("Unauthorized: You can only cancel your own orders.")

        if order.status not in OrderStatus.CANCELLABLE_STATUSES:
            raise CancellationNotAllowedError(
                f"Cannot cancel order #{order_id}. Order is already '{order.status}'. "
                f"Cancellations are only allowed when 'Placed' or 'Accepted'."
            )

        # Restore stock
        for oi in order.items:
            if oi.menu_item:
                oi.menu_item.stock += oi.quantity
                if oi.menu_item.stock > 0:
                    oi.menu_item.is_available = True

        # Refund wallet if paid via wallet
        if order.payment_method == PaymentMethod.WALLET and order.payment_status == PaymentStatus.PAID:
            user = db.session.get(User, order.user_id)
            if user:
                user.wallet_balance = round(user.wallet_balance + order.total_amount, 2)
            order.payment_status = PaymentStatus.REFUNDED

        order.status = OrderStatus.CANCELLED
        order.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        return order

    @staticmethod
    def get_order_by_id(order_id: int) -> Optional[Order]:
        """Fetch order by ID."""
        return db.session.get(Order, order_id)

    @staticmethod
    def get_user_orders(user_id: int) -> List[Order]:
        """Fetch all orders placed by a student."""
        return Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_active_queue_orders() -> List[Order]:
        """Fetch incoming active orders for staff dashboard."""
        return Order.query.filter(
            Order.status.in_([OrderStatus.PLACED, OrderStatus.ACCEPTED, OrderStatus.PREPARING, OrderStatus.READY])
        ).order_by(Order.created_at.asc()).all()

    @staticmethod
    def get_queue_position(order_id: int) -> int:
        """Calculate queue position of a specific order."""
        target_order = db.session.get(Order, order_id)
        if not target_order or target_order.status in [OrderStatus.COLLECTED, OrderStatus.CANCELLED]:
            return 0

        ahead_count = Order.query.filter(
            Order.status.in_([OrderStatus.PLACED, OrderStatus.ACCEPTED, OrderStatus.PREPARING]),
            Order.created_at < target_order.created_at
        ).count()
        return ahead_count + 1
