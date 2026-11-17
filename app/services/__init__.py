"""Services package exports."""
from app.services.auth_service import AuthService, login_required, roles_accepted, AuthenticationError
from app.services.menu_service import MenuService
from app.services.order_service import (
    OrderService,
    OrderError,
    OutOfStockError,
    InvalidSlotError,
    DuplicateOrderError,
    InsufficientFundsError,
    CancellationNotAllowedError,
)
from app.services.report_service import ReportService

__all__ = [
    "AuthService",
    "login_required",
    "roles_accepted",
    "AuthenticationError",
    "MenuService",
    "OrderService",
    "OrderError",
    "OutOfStockError",
    "InvalidSlotError",
    "DuplicateOrderError",
    "InsufficientFundsError",
    "CancellationNotAllowedError",
    "ReportService",
]
