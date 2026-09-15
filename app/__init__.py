"""
RepRequest application factory.

This module constructs and configures the Flask application.
Feature-specific behavior should live elsewhere in the app package.
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

    # Flask automatically looks for:
    # app/templates/
    # app/static/
    app = Flask(
        __name__,
        instance_path=str(project_root / "instance")
    )

    # Load application configuration
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register application routes
    from app.routes import register_routes
    register_routes(app)

    # Temporary database initialization.
    # Flask-Migrate will replace this later.
    with app.app_context():
        db.create_all()

    return app