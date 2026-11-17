"""Admin routes for daily sales reports and CSV exports."""
from datetime import datetime
from flask import Blueprint, render_template, request, Response, flash
from app.services.auth_service import login_required, roles_accepted
from app.services.report_service import ReportService

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/dashboard")
@login_required
@roles_accepted("admin")
def dashboard():
    """Admin sales analytics dashboard."""
    date_str = request.args.get("date")
    target_date = None

    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Using today's metrics.", "warning")

    summary = ReportService.get_sales_summary(target_date)
    return render_template(
        "admin/dashboard.html",
        summary=summary,
        selected_date=date_str or ""
    )


@admin_bp.route("/sales/csv")
@login_required
@roles_accepted("admin")
def export_sales_csv():
    """Download daily sales report as CSV."""
    date_str = request.args.get("date")
    target_date = None
    if date_str:
        try:
            target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    csv_data = ReportService.generate_sales_csv(target_date)
    filename = f"canteen_sales_{date_str if date_str else 'all_time'}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
