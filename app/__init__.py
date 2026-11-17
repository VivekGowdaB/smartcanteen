"""Application factory module for Smart Canteen Ordering System."""
import logging
import os
from flask import Flask, jsonify, render_template, session
from app.config import config_by_name
from app.extensions import db
from app.models.user import User


def create_app(config_name: str = None) -> Flask:
    """Create and configure an instance of the Flask application."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development").lower()

    app = Flask(__name__)
    app_config = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(app_config)

    # Initialize extensions
    db.init_app(app)

    # Configure structured logging
    logging.basicConfig(
        level=logging.INFO if not app.config.get("DEBUG") else logging.DEBUG,
        format="[%(asctime)s] %(levelname)s in %(module)s: %(message)s"
    )

    # Context processor to inject user information into templates
    @app.context_processor
    def inject_current_user():
        user = None
        if "user_id" in session:
            user = db.session.get(User, session["user_id"])
        return dict(current_user=user)

    # Register Blueprints
    from app.routes import auth_bp, student_bp, staff_bp, admin_bp, api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Root /health alias for Kubernetes probes and external pingers
    @app.route("/health")
    def root_health():
        from app.routes.api import health
        return health()

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        if app.config.get("TESTING") or request_is_json():
            return jsonify({"error": "Bad request", "details": str(error)}), 400
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        if app.config.get("TESTING") or request_is_json():
            return jsonify({"error": "Forbidden", "details": "Insufficient permissions"}), 403
        return render_template("errors/403.html"), 403

    @app.errorhandler(404)
    def not_found(error):
        if app.config.get("TESTING") or request_is_json():
            return jsonify({"error": "Not found"}), 404
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if app.config.get("TESTING") or request_is_json():
            return jsonify({"error": "Internal server error"}), 500
        return render_template("errors/500.html"), 500

    def request_is_json():
        from flask import request
        return request.is_json or request.path.startswith("/api/")

    return app
