"""
Company database model for RepRequest.

A Company represents one organization using RepRequest.
Users, machines, repair requests, and other company-owned
resources are associated with a Company through company_id.
"""

from datetime import datetime

from app.extensions import db


class Company(db.Model):
    """
    Organization account within RepRequest.
    """

    __tablename__ = "company"

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(100),
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # Allows:
    #
    # company.users
    #
    # and, through the backref:
    #
    # user.company
    users = db.relationship(
        "User",
        backref="company",
        lazy=True
    )