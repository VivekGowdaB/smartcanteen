"""Student routes for menu browsing, cart, checkout, live order status, and history."""
import json
import uuid
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.services.auth_service import login_required
from app.services.menu_service import MenuService
from app.services.order_service import (
    OrderService, OrderError, OutOfStockError, InvalidSlotError, InsufficientFundsError,
    CancellationNotAllowedError, DuplicateOrderError
)
from app.models.user import User
from app.extensions import db

student_bp = Blueprint("student", __name__)


@student_bp.route("/")
@student_bp.route("/menu")
def menu_view():
    """Browse menu with category filters and search."""
    category_id = request.args.get("category_id", type=int)
    search_query = request.args.get("q", type=str)

    categories = MenuService.get_categories()
    items = MenuService.get_menu_items(
        category_id=category_id,
        search_query=search_query,
        available_only=False
    )

    return render_template(
        "student/menu.html",
        categories=categories,
        items=items,
        selected_category=category_id,
        search_query=search_query or ""
    )


@student_bp.route("/cart")
def cart_view():
    """View cart page."""
    return render_template("student/cart.html")


@student_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout_view():
    """Checkout page: choose pickup slot and mock payment method."""
    slots = OrderService.get_pickup_slots()
    user = db.session.get(User, session["user_id"])

    if request.method == "POST":
        pickup_slot = request.form.get("pickup_slot")
        payment_method = request.form.get("payment_method")
        cart_data_raw = request.form.get("cart_data", "[]")
        idempotency_key = request.form.get("idempotency_key") or str(uuid.uuid4())

        try:
            items = json.loads(cart_data_raw)
        except json.JSONDecodeError:
            flash("Invalid cart data submitted.", "danger")
            return redirect(url_for("student.cart_view"))

        if not items:
            flash("Your cart is empty. Please add items to checkout.", "warning")
            return redirect(url_for("student.menu_view"))

        try:
            order = OrderService.place_order(
                user_id=user.id,
                items=items,
                pickup_slot=pickup_slot,
                payment_method=payment_method,
                idempotency_key=idempotency_key,
            )
            flash(f"Order #{order.id} placed successfully!", "success")
            return redirect(url_for("student.order_status_view", order_id=order.id))

        except (OutOfStockError, InvalidSlotError, InsufficientFundsError, DuplicateOrderError, OrderError) as e:
            flash(str(e), "danger")
            return render_template("student/checkout.html", slots=slots, user=user)

    return render_template("student/checkout.html", slots=slots, user=user)


@student_bp.route("/orders/<int:order_id>")
@login_required
def order_status_view(order_id: int):
    """Live order status tracking page with 5s polling."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        flash(f"Order #{order_id} not found.", "danger")
        return redirect(url_for("student.history_view"))

    # Authorize: student can only view their own order, staff/admin can view any
    if session.get("role") == "student" and order.user_id != session.get("user_id"):
        flash("You are not authorized to view this order.", "danger")
        return redirect(url_for("student.history_view"))

    queue_pos = OrderService.get_queue_position(order_id)
    return render_template("student/order_status.html", order=order, queue_position=queue_pos)


@student_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order_view(order_id: int):
    """Cancel order if allowed."""
    try:
        OrderService.cancel_order(order_id, user_id=session.get("user_id"))
        flash(f"Order #{order_id} has been cancelled.", "info")
    except (CancellationNotAllowedError, OrderError) as e:
        flash(str(e), "danger")

    return redirect(url_for("student.order_status_view", order_id=order_id))


@student_bp.route("/history")
@login_required
def history_view():
    """Order history for the logged-in student."""
    orders = OrderService.get_user_orders(session["user_id"])
    return render_template("student/history.html", orders=orders)
