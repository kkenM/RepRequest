"""
User database model for RepRequest.

Every authenticated RepRequest user belongs to one Company.
User roles determine what functionality the account may access.
"""

from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from app.extensions import db


class User(UserMixin, db.Model):
    """
    Authenticated RepRequest user.
    """

    __tablename__ = "user"

    # User authorization roles
    ROLE_COMPANY_ADMIN = "company-admin"
    ROLE_EMPLOYEE_CREW = "employee-crew"
    ROLE_EMPLOYEE_TECHNICIAN = "employee-technician"

    # Roles that company administrators may assign
    # to employee accounts.
    EMPLOYEE_ROLES = (
        ROLE_EMPLOYEE_CREW,
        ROLE_EMPLOYEE_TECHNICIAN
    )

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

    def set_password(self, password):
        """
        Securely hash and store a user's password.
        """

        self.password_hash = generate_password_hash(
            password
        )

    def check_password(self, password):
        """
        Verify a plaintext password against the
        user's stored password hash.
        """

        return check_password_hash(
            self.password_hash,
            password
        )