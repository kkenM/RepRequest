"""
Configuration settings for RepRequest.

Development defaults are provided for local use. Production
security settings will be strengthened during the security
cleanup phase.
"""

import os
from datetime import timedelta

class Config:
    # Used by Flask to securely sign session cookies.
    #
    # The fallback value is for local development only.
    # Production must use an environment variable.
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-secret-key-change-before-production"
    )

    # Local development database
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL",
        "sqlite:///accounts.db"
    )

    # Disable unnecessary SQLAlchemy event tracking
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Sign users out after 12 hours without activity.
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SESSION_REFRESH_EACH_REQUEST = True

    # JavaScript can't read the cookie.
    SESSION_COOKIE_HTTPONLY = True

    # Cookie isn't sent on cross-site form posts.
    SESSION_COOKIE_SAME_SITE = "Lax"

    # HTTPS only.
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE") == "1"
    )

    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAME_SITE = "Lax"
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SAME_SITE

class TestingConfig(Config):
    """
    Configuration used by the automated test suite.

    Tests use a temporary in-memory SQLite database so they
    never modify the developer's normal accounts.db database.
    """

    TESTING = True

    SECRET_KEY = "test-secret-key"

    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"