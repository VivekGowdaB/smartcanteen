"""Menu service for managing food categories and items."""
from typing import List, Optional
from app.extensions import db
from app.models.menu import Category, MenuItem


class MenuService:
    @staticmethod
    def get_categories() -> List[Category]:
        """Fetch all food categories."""
        return Category.query.order_by(Category.name.asc()).all()

    @staticmethod
    def get_menu_items(category_id: Optional[int] = None, search_query: Optional[str] = None,
                       available_only: bool = False) -> List[MenuItem]:
        """Retrieve menu items with optional category and search filters."""
        query = MenuItem.query

        if category_id:
            query = query.filter(MenuItem.category_id == category_id)

        if search_query:
            term = f"%{search_query.strip()}%"
            query = query.filter(MenuItem.name.ilike(term) | MenuItem.description.ilike(term))

        if available_only:
            query = query.filter(MenuItem.is_available.is_(True), MenuItem.stock > 0)

        return query.order_by(MenuItem.name.asc()).all()

    @staticmethod
    def get_item_by_id(item_id: int) -> Optional[MenuItem]:
        """Retrieve a specific menu item."""
        return db.session.get(MenuItem, item_id)

    @staticmethod
    def create_menu_item(category_id: int, name: str, description: str, price: float,
                         stock: int = 10, prep_time_minutes: int = 10) -> MenuItem:
        """Create a new menu item."""
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        if stock < 0:
            raise ValueError("Stock cannot be negative.")

        item = MenuItem(
            category_id=category_id,
            name=name.strip(),
            description=description.strip() if description else "",
            price=float(price),
            stock=int(stock),
            is_available=(stock > 0),
            prep_time_minutes=max(1, int(prep_time_minutes)),
        )
        db.session.add(item)
        db.session.commit()
        return item

    @staticmethod
    def update_menu_item(item_id: int, **kwargs) -> MenuItem:
        """Update fields on a menu item."""
        item = db.session.get(MenuItem, item_id)
        if not item:
            raise ValueError("Menu item not found.")

        if "price" in kwargs and kwargs["price"] is not None:
            if float(kwargs["price"]) <= 0:
                raise ValueError("Price must be greater than zero.")
            item.price = float(kwargs["price"])

        if "stock" in kwargs and kwargs["stock"] is not None:
            stock_val = int(kwargs["stock"])
            if stock_val < 0:
                raise ValueError("Stock cannot be negative.")
            item.stock = stock_val
            # Auto update availability if stock is 0
            if item.stock == 0:
                item.is_available = False

        if "name" in kwargs and kwargs["name"]:
            item.name = kwargs["name"].strip()

        if "description" in kwargs:
            item.description = kwargs["description"]

        if "prep_time_minutes" in kwargs and kwargs["prep_time_minutes"] is not None:
            item.prep_time_minutes = max(1, int(kwargs["prep_time_minutes"]))

        if "is_available" in kwargs and kwargs["is_available"] is not None:
            item.is_available = bool(kwargs["is_available"])

        db.session.commit()
        return item

    @staticmethod
    def toggle_availability(item_id: int) -> MenuItem:
        """Toggle the is_available flag for an item."""
        item = db.session.get(MenuItem, item_id)
        if not item:
            raise ValueError("Menu item not found.")

        item.is_available = not item.is_available
        db.session.commit()
        return item

    @staticmethod
    def update_stock(item_id: int, new_stock: int) -> MenuItem:
        """Update the stock count of an item, setting is_available=False if stock is 0."""
        return MenuService.update_menu_item(item_id, stock=new_stock)
