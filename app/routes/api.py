"""REST API routes for programmatic access and frontend AJAX polling."""
from datetime import datetime, timezone
from flask import Blueprint, jsonify, request, session
from app.extensions import db
from app.services.auth_service import login_required, roles_accepted
from app.services.menu_service import MenuService
from app.services.order_service import (
    OrderService, OrderError, OutOfStockError, InvalidSlotError, InsufficientFundsError,
    DuplicateOrderError, CancellationNotAllowedError
)
from app.services.report_service import ReportService

api_bp = Blueprint("api", __name__, url_prefix="/api")


@api_bp.route("/health")
def health():
    """Liveness and readiness probe endpoint for Docker and Kubernetes."""
    db_status = "connected"
    try:
        db.session.execute(db.text("SELECT 1"))
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        return jsonify({
            "status": "degraded",
            "database": db_status,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }), 503

    return jsonify({
        "status": "healthy",
        "service": "smart-canteen-ordering-system",
        "database": db_status,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }), 200


@api_bp.route("/menu")
def get_menu():
    """Retrieve menu items as JSON."""
    category_id = request.args.get("category_id", type=int)
    search = request.args.get("q", type=str)
    available_only = request.args.get("available_only", "false").lower() == "true"

    items = MenuService.get_menu_items(
        category_id=category_id,
        search_query=search,
        available_only=available_only
    )
    return jsonify([i.to_dict() for i in items]), 200


@api_bp.route("/slots")
def get_slots():
    """Retrieve active pickup slots and capacities."""
    slots = OrderService.get_pickup_slots()
    return jsonify(slots), 200


@api_bp.route("/orders", methods=["POST"])
@login_required
def create_order():
    """Create a new order from JSON payload."""
    data = request.get_json(silent=True) or {}
    items = data.get("items", [])
    pickup_slot = data.get("pickup_slot")
    payment_method = data.get("payment_method", "Cash on Pickup")
    idempotency_key = data.get("idempotency_key")

    if not items:
        return jsonify({"error": "Cart is empty."}), 400

    if not pickup_slot:
        return jsonify({"error": "Pickup slot is required."}), 400

    try:
        order = OrderService.place_order(
            user_id=session["user_id"],
            items=items,
            pickup_slot=pickup_slot,
            payment_method=payment_method,
            idempotency_key=idempotency_key,
        )
        return jsonify({
            "message": "Order created successfully",
            "order": order.to_dict()
        }), 201

    except OutOfStockError as e:
        return jsonify({"error": str(e), "code": "OUT_OF_STOCK"}), 409
    except InvalidSlotError as e:
        return jsonify({"error": str(e), "code": "INVALID_SLOT"}), 400
    except InsufficientFundsError as e:
        return jsonify({"error": str(e), "code": "INSUFFICIENT_FUNDS"}), 402
    except DuplicateOrderError as e:
        return jsonify({"error": str(e), "code": "DUPLICATE_ORDER"}), 409
    except OrderError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/orders/<int:order_id>/status")
@login_required
def get_order_status(order_id: int):
    """Poll live order status, queue position, and estimated wait time."""
    order = OrderService.get_order_by_id(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    # Security check: student can only check own order
    if session.get("role") == "student" and order.user_id != session.get("user_id"):
        return jsonify({"error": "Forbidden"}), 403

    queue_pos = OrderService.get_queue_position(order_id)
    data = order.to_dict()
    data["queue_position"] = queue_pos

    return jsonify(data), 200


@api_bp.route("/orders/<int:order_id>/cancel", methods=["POST"])
@login_required
def cancel_order(order_id: int):
    """Cancel order via JSON endpoint."""
    user_id = session.get("user_id") if session.get("role") == "student" else None
    try:
        order = OrderService.cancel_order(order_id, user_id=user_id)
        return jsonify({
            "message": "Order cancelled successfully",
            "order": order.to_dict()
        }), 200
    except CancellationNotAllowedError as e:
        return jsonify({"error": str(e), "code": "CANCELLATION_DISALLOWED"}), 400
    except OrderError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/staff/orders/<int:order_id>/status", methods=["POST"])
@login_required
@roles_accepted("staff", "admin")
def staff_update_status(order_id: int):
    """Update order status programmatically."""
    data = request.get_json(silent=True) or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    try:
        order = OrderService.update_order_status(order_id, new_status)
        return jsonify({
            "message": "Status updated successfully",
            "order": order.to_dict()
        }), 200
    except OrderError as e:
        return jsonify({"error": str(e)}), 400


@api_bp.route("/admin/sales")
@login_required
@roles_accepted("admin")
def get_sales():
    """Retrieve sales summary as JSON."""
    date_str = request.args.get("date")
    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    summary = ReportService.get_sales_summary(target_date)
    return jsonify(summary), 200
