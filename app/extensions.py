"""
Shared Flask extensions for RepRequest.

Extension objects are created here without being attached to a
specific Flask application. The application factory connects them
to the application when RepRequest starts.
"""

from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy


# Database extension
db = SQLAlchemy()


# Authentication/session extension
login_manager = LoginManager()

# Redirect unauthenticated users to the login page
login_manager.login_view = "login"