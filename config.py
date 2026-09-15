"""
Configuration settings for RepRequest.

Development defaults are provided for local use. Production
security settings will be strengthened during the security
cleanup phase.
"""

import os


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