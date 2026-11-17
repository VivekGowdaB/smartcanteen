"""Menu management and browsing tests."""
import pytest
from app.services.menu_service import MenuService


def test_menu_query_and_search(app, seed_menu):
    """Test menu item filtering and search logic."""
    with app.app_context():
        # Get all items
        all_items = MenuService.get_menu_items()
        assert len(all_items) == 3

        # Available only
        available_items = MenuService.get_menu_items(available_only=True)
        assert len(available_items) == 2

        # Filter by search term 'chai'
        chai_items = MenuService.get_menu_items(search_query="chai")
        assert len(chai_items) == 1
        assert chai_items[0].name == "Masala Chai"

        # Filter by category
        cat_id = seed_menu["category"].id
        cat_items = MenuService.get_menu_items(category_id=cat_id)
        assert len(cat_items) == 3


def test_stock_update_auto_sold_out(app, seed_menu):
    """Test stock updates and auto-marking as unavailable when stock hits 0."""
    with app.app_context():
        item1_id = seed_menu["item1"].id

        # Update stock to positive
        updated = MenuService.update_stock(item1_id, 15)
        assert updated.stock == 15
        assert updated.is_available is True

        # When stock hits 0, item is auto-marked as unavailable
        depleted = MenuService.update_stock(item1_id, 0)
        assert depleted.stock == 0
        assert depleted.is_available is False
        assert depleted.is_in_stock is False


def test_menu_validation(app, seed_menu):
    """Test invalid price or negative stock validation."""
    with app.app_context():
        cat_id = seed_menu["category"].id

        # Negative price
        with pytest.raises(ValueError, match="Price must be greater than zero"):
            MenuService.create_menu_item(cat_id, "Bad Item", "Desc", price=-10.0, stock=5)

        # Negative stock
        with pytest.raises(ValueError, match="Stock cannot be negative"):
            MenuService.create_menu_item(cat_id, "Bad Stock Item", "Desc", price=25.0, stock=-3)


def test_api_menu_endpoint(client, seed_menu):
    """Test /api/menu REST endpoint."""
    res = client.get("/api/menu")
    assert res.status_code == 200
    data = res.get_json()
    assert isinstance(data, list)
    assert len(data) == 3

    # Test available_only parameter
    avail_res = client.get("/api/menu?available_only=true")
    avail_data = avail_res.get_json()
    assert len(avail_data) == 2
