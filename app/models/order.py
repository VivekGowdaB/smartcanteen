"""Order, OrderItem, and PickupSlotConfig models."""
from datetime import datetime, timezone
from app.extensions import db


class OrderStatus:
    PLACED = "Placed"
    ACCEPTED = "Accepted"
    PREPARING = "Preparing"
    READY = "Ready"
    COLLECTED = "Collected"
    CANCELLED = "Cancelled"

    ALL_STATUSES = [PLACED, ACCEPTED, PREPARING, READY, COLLECTED, CANCELLED]
    CANCELLABLE_STATUSES = [PLACED, ACCEPTED]


class PaymentMethod:
    WALLET = "Wallet"
    UPI = "UPI"
    CASH = "Cash on Pickup"

    ALL_METHODS = [WALLET, UPI, CASH]


class PaymentStatus:
    PAID = "Paid"
    PENDING = "Pending"
    REFUNDED = "Refunded"


class Order(db.Model):
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    status = db.Column(db.String(30), nullable=False, default=OrderStatus.PLACED, index=True)
    pickup_slot = db.Column(db.String(50), nullable=False, index=True)
    payment_method = db.Column(db.String(30), nullable=False, default=PaymentMethod.CASH)
    payment_status = db.Column(db.String(30), nullable=False, default=PaymentStatus.PENDING)
    total_amount = db.Column(db.Float, nullable=False, default=0.0)
    estimated_wait_minutes = db.Column(db.Integer, nullable=False, default=15)
    idempotency_key = db.Column(db.String(100), unique=True, nullable=True, index=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )

    # Relationships
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "customer_name": self.user.username if self.user else None,
            "status": self.status,
            "pickup_slot": self.pickup_slot,
            "payment_method": self.payment_method,
            "payment_status": self.payment_status,
            "total_amount": round(self.total_amount, 2),
            "estimated_wait_minutes": self.estimated_wait_minutes,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else None,
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S") if self.updated_at else None,
            "items": [item.to_dict() for item in self.items],
        }

    def __repr__(self) -> str:
        return f"<Order #{self.id} Status: {self.status} Total: {self.total_amount}>"


class OrderItem(db.Model):
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id"), nullable=False, index=True)
    menu_item_id = db.Column(db.Integer, db.ForeignKey("menu_items.id"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    unit_price = db.Column(db.Float, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    # Relationships
    order = db.relationship("Order", back_populates="items")
    menu_item = db.relationship("MenuItem", back_populates="order_items")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "menu_item_id": self.menu_item_id,
            "item_name": self.menu_item.name if self.menu_item else "Unknown Item",
            "quantity": self.quantity,
            "unit_price": round(self.unit_price, 2),
            "subtotal": round(self.subtotal, 2),
        }

    def __repr__(self) -> str:
        return f"<OrderItem ItemID: {self.menu_item_id} Qty: {self.quantity}>"


class PickupSlotConfig(db.Model):
    __tablename__ = "pickup_slot_configs"

    id = db.Column(db.Integer, primary_key=True)
    slot_time = db.Column(db.String(50), unique=True, nullable=False)
    max_orders = db.Column(db.Integer, nullable=False, default=10)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "slot_time": self.slot_time,
            "max_orders": self.max_orders,
            "is_active": self.is_active,
        }
