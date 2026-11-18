import os

BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    f"sqlite:///{os.path.join(BASE_DIR, 'canteen.db')}"
)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)


class Config:
    """Base configuration with sensible defaults."""
    SECRET_KEY = os.environ.get("SECRET_KEY", "smart-canteen-dev-secret-key-2026")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_ORDERS_PER_SLOT = int(os.environ.get("MAX_ORDERS_PER_SLOT", 10))
    # Database URL configuration (defaults to SQLite in local instance dir)
    SQLALCHEMY_DATABASE_URI = DATABASE_URL


class DevelopmentConfig(Config):
    """Development environment specific configuration."""
    DEBUG = True


class TestingConfig(Config):
    """Testing configuration with in-memory database."""
    TESTING = True
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    # In production, require secure secret key if possible
    SECRET_KEY = os.environ.get("SECRET_KEY", "production-must-set-secret-key")


config_by_name = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
