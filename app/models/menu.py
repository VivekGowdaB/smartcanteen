"""Category and MenuItem models for canteen food management."""
from datetime import datetime, timezone
from app.extensions import db


class Category(db.Model):
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False, index=True)
    description = db.Column(db.String(255), nullable=True)

    items = db.relationship("MenuItem", back_populates="category", lazy=True, cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "item_count": len(self.items) if self.items else 0,
        }

    def __repr__(self) -> str:
        return f"<Category {self.name}>"


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)
    is_available = db.Column(db.Boolean, nullable=False, default=True)
    prep_time_minutes = db.Column(db.Integer, nullable=False, default=10)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    category = db.relationship("Category", back_populates="items")
    order_items = db.relationship("OrderItem", back_populates="menu_item", lazy=True)

    @property
    def is_in_stock(self) -> bool:
        """Determines if the item is physically available to purchase."""
        return self.is_available and self.stock > 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category_id": self.category_id,
            "category_name": self.category.name if self.category else None,
            "name": self.name,
            "description": self.description,
            "price": round(self.price, 2),
            "stock": self.stock,
            "is_available": self.is_available,
            "is_in_stock": self.is_in_stock,
            "prep_time_minutes": self.prep_time_minutes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<MenuItem {self.name} (Stock: {self.stock})>"
