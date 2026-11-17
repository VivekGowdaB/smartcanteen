"""User model definition with role-based access control."""
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")  # student, staff, admin
    wallet_balance = db.Column(db.Float, nullable=False, default=500.0)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    orders = db.relationship("Order", back_populates="user", lazy=True, cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash and store the user password."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify the user password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        """Serialize user to dictionary (excluding sensitive password hash)."""
        return {
            "id": self.id,
            "username": self.username,
            "email": self.email,
            "role": self.role,
            "wallet_balance": round(self.wallet_balance, 2),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:
        return f"<User {self.username} ({self.role})>"
