"""
RepRequest application factory.

This module constructs and configures the Flask application.
Feature-specific behavior should live in dedicated Blueprints.
"""

from pathlib import Path

from flask import Flask

from config import Config
from app.extensions import db, login_manager


def create_app(config_class=Config):
    """
    Create and configure a RepRequest Flask application.
    """

    # Path to the RepRequest project root
    project_root = Path(__file__).resolve().parent.parent

    app = Flask(
        __name__,
        instance_path=str(project_root / "instance")
    )

    # Load application configuration
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Import Blueprints after extensions have been initialized
    # to avoid circular-import problems.
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp

    # Register application feature modules
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # Ensure SQLAlchemy knows about all RepRequest models
    # before creating database tables.
    from app.models import Company, User

    # Temporary database initialization.
    # Flask-Migrate will replace this in a later step.
    with app.app_context():
        db.create_all()

    return app