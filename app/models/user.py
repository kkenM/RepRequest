"""
User database model for RepRequest.

Every authenticated RepRequest user belongs to one Company.
User roles determine what functionality the account may access.
"""

import secrets
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from app.extensions import db
from app.roles import (
    COMPANY_ADMIN,
    EMPLOYEE_ROLES,
    ROLE_LABELS
)

def generate_session_token():
    """
    Return a new random, URL-safe session token.
    """
    return secrets.token_urlsafe(32)

class User(UserMixin, db.Model):
    """
    Authenticated RepRequest user.
    """

    __tablename__ = "user"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.id"),
        nullable=False
    )

    first_name = db.Column(
        db.String(50),
        nullable=False
    )

    last_name = db.Column(
        db.String(50),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    role = db.Column(
        db.String(30),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Flask-login stores this in the session cookie
    session_token = db.Column(
        db.String(64),
        unique=True,
        nullable=False,
        default=generate_session_token
    )

    def get_id(self):
        """
        Return the value Flask-Login stores in the session cookie.
        Overrides UserMixin.get_id(), which would return self.id.
        """

        return self.session_token

    def rotate_session_token(self):
        """
        Invalidate every existing session for this user.
        The caller must commit the change.
        """

        self.session_token = generate_session_token()

    def set_password(self, password):
        """
        Securely hash and store a user's password.
        """

        self.password_hash = generate_password_hash(
            password
        )

        self.rotate_session_token()

    def check_password(self, password):
        """
        Verify a plaintext password against the
        user's stored password hash.
        """

        return check_password_hash(
            self.password_hash,
            password
        )

    @property
    def is_company_admin(self):
        """
        Return True when the user has company-administrator
        privileges.
        """

        return self.role == COMPANY_ADMIN

    @property
    def is_employee(self):
        """
        Return True when the account uses an employee role.
        """

        return self.role in EMPLOYEE_ROLES

    @property
    def role_label(self):
        """
        Return a human-readable version of the user's role.
        """

        return ROLE_LABELS.get(
            self.role,
            self.role
        )