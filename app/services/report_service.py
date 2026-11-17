"""Reporting service for sales analytics and CSV export."""
import csv
import io
from datetime import datetime, date
from typing import Dict, Any, Optional
from sqlalchemy import func
from app.extensions import db
from app.models.order import Order, OrderItem, OrderStatus, PaymentStatus
from app.models.menu import MenuItem


class ReportService:
    @staticmethod
    def get_sales_summary(target_date: Optional[date] = None) -> Dict[str, Any]:
        """Aggregate sales metrics for a given date or all-time."""
        query = Order.query

        if target_date:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            query = query.filter(Order.created_at >= start_of_day, Order.created_at <= end_of_day)

        all_orders = query.all()

        total_orders = len(all_orders)
        collected_or_paid = [
            o for o in all_orders
            if o.status == OrderStatus.COLLECTED or o.payment_status == PaymentStatus.PAID
        ]
        cancelled_orders = [o for o in all_orders if o.status == OrderStatus.CANCELLED]

        total_revenue = sum(o.total_amount for o in collected_or_paid)

        # Status counts
        status_counts = {}
        for s in OrderStatus.ALL_STATUSES:
            status_counts[s] = sum(1 for o in all_orders if o.status == s)

        # Payment methods count
        payment_counts = {}
        for o in all_orders:
            payment_counts[o.payment_method] = payment_counts.get(o.payment_method, 0) + 1

        # Slot distribution
        slot_counts = {}
        for o in all_orders:
            slot_counts[o.pickup_slot] = slot_counts.get(o.pickup_slot, 0) + 1

        # Top selling items
        top_items_query = (
            db.session.query(
                MenuItem.name,
                func.sum(OrderItem.quantity).label("total_sold"),
                func.sum(OrderItem.subtotal).label("item_revenue")
            )
            .join(OrderItem, MenuItem.id == OrderItem.menu_item_id)
            .join(Order, Order.id == OrderItem.order_id)
            .filter(Order.status != OrderStatus.CANCELLED)
        )
        if target_date:
            top_items_query = top_items_query.filter(
                Order.created_at >= start_of_day,
                Order.created_at <= end_of_day
            )

        top_items = (
            top_items_query.group_by(MenuItem.name)
            .order_by(func.sum(OrderItem.quantity).desc())
            .limit(5)
            .all()
        )

        top_items_data = [
            {"name": name, "sold": int(sold or 0), "revenue": round(float(rev or 0), 2)}
            for name, sold, rev in top_items
        ]

        return {
            "date": target_date.strftime("%Y-%m-%d") if target_date else "All Time",
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "cancelled_count": len(cancelled_orders),
            "status_counts": status_counts,
            "payment_counts": payment_counts,
            "slot_counts": slot_counts,
            "top_items": top_items_data,
        }

    @staticmethod
    def generate_sales_csv(target_date: Optional[date] = None) -> str:
        """Export orders to CSV string."""
        query = Order.query.order_by(Order.created_at.desc())
        if target_date:
            start_of_day = datetime.combine(target_date, datetime.min.time())
            end_of_day = datetime.combine(target_date, datetime.max.time())
            query = query.filter(Order.created_at >= start_of_day, Order.created_at <= end_of_day)

        orders = query.all()

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Order ID", "Date Time (UTC)", "Customer", "Pickup Slot",
            "Payment Method", "Payment Status", "Items Ordered", "Total Amount (INR)", "Status"
        ])

        for o in orders:
            items_str = "; ".join([f"{oi.menu_item.name if oi.menu_item else 'Item'} x{oi.quantity}" for oi in o.items])
            writer.writerow([
                o.id,
                o.created_at.strftime("%Y-%m-%d %H:%M:%S") if o.created_at else "",
                o.user.username if o.user else "Unknown",
                o.pickup_slot,
                o.payment_method,
                o.payment_status,
                items_str,
                f"{o.total_amount:.2f}",
                o.status
            ])

        return output.getvalue()
