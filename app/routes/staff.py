"""Staff dashboard routes for kitchen operations and stock management."""
from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.services.auth_service import login_required, roles_accepted
from app.services.order_service import OrderService, OrderError, OrderStatus
from app.services.menu_service import MenuService
from app.models.menu import Category

staff_bp = Blueprint("staff", __name__, url_prefix="/staff")


@staff_bp.route("/dashboard")
@login_required
@roles_accepted("staff", "admin")
def dashboard():
    """Live kitchen dashboard showing active orders in queue."""
    orders = OrderService.get_active_queue_orders()
    return render_template(
        "staff/dashboard.html",
        orders=orders,
        statuses=OrderStatus.ALL_STATUSES
    )


@staff_bp.route("/orders/<int:order_id>/status", methods=["POST"])
@login_required
@roles_accepted("staff", "admin")
def update_status(order_id: int):
    """Transition order status."""
    new_status = request.form.get("status")
    try:
        OrderService.update_order_status(order_id, new_status)
        flash(f"Order #{order_id} transitioned to '{new_status}'.", "success")
    except OrderError as e:
        flash(str(e), "danger")

    return redirect(url_for("staff.dashboard"))


@staff_bp.route("/menu", methods=["GET", "POST"])
@login_required
@roles_accepted("staff", "admin")
def menu_management():
    """View and update stock levels and item availability."""
    if request.method == "POST":
        action = request.form.get("action")
        item_id = request.form.get("item_id", type=int)

        try:
            if action == "update_stock":
                new_stock = request.form.get("stock", type=int)
                MenuService.update_stock(item_id, new_stock)
                flash(f"Stock updated for item #{item_id}.", "success")
            elif action == "toggle_availability":
                MenuService.toggle_availability(item_id)
                flash(f"Availability toggled for item #{item_id}.", "info")
            elif action == "add_item":
                category_id = request.form.get("category_id", type=int)
                name = request.form.get("name")
                desc = request.form.get("description")
                price = request.form.get("price", type=float)
                stock = request.form.get("stock", type=int)
                prep_time = request.form.get("prep_time_minutes", type=int)
                MenuService.create_menu_item(category_id, name, desc, price, stock, prep_time)
                flash(f"Added new menu item '{name}'.", "success")
        except ValueError as e:
            flash(str(e), "danger")

        return redirect(url_for("staff.menu_management"))

    items = MenuService.get_menu_items()
    categories = Category.query.all()
    return render_template("staff/menu_manage.html", items=items, categories=categories)
