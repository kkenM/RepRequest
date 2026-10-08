"""
RepRequest application factory.

This module assembles the Flask application by loading configuration,
initializing extensions, registering Blueprints, and installing global
error handlers.

Do not place feature-specific routes or business logic in this module.
Feature behavior should live in Blueprints and services.
"""

from datetime import datetime
from pathlib import Path

from flask import Flask, request

from config import Config
from app.extensions import db, login_manager, migrate

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

    migrate.init_app(
        app,
        db
    )

    # Import Blueprints after extensions have been initialized
    # to avoid circular-import problems.
    from app.main.routes import main_bp
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.machines.routes import machines_bp
    from app.repairs.routes import repairs_bp
    from app.logs.routes import logs_bp

    # Register application feature modules
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(machines_bp)
    app.register_blueprint(repairs_bp)
    app.register_blueprint(logs_bp)

    # Values every template may use, such as the footer copyright year.
    @app.context_processor
    def inject_template_globals():
        return {
            "now_year": datetime.utcnow().year
        }


    # SECURITY: Don't let browser keep caches of pages
    @app.after_request
    def prevent_page_caching(response):
        if request.endpoint != "static":
            response.headers["Cache-Control"] = "no-store"
        return response

    # Register application-wide error handling
    from app.errors import register_error_handlers
    register_error_handlers(app)

    # Ensure SQLAlchemy knows about all RepRequest models
    # before creating database tables.
    from app.models import Company, User

    '''
    # SECURITY: Prevents public sign session cookies
    # ENABLE LATER
    if (
        not app.debug
        and not app.testing
        and app.config["SECRET_KEY"] == "dev-secret-key-change-before-production"
    ):
        raise RuntimeError(
            "Set the SECRET_KEY environment variable before running in production"
        )
    '''

    return app