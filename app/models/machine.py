# Needed to generate the random public ID.
import secrets
from datetime import datetime

from app.extensions import db


# Makes the random ID for the QR Code
def generate_public_id():

    # Safe characters
    return secrets.token_urlsafe(9)


# A machine owned by a company
class Machine(db.Model):

    __tablename__ = "machine"

    # Internal database ID. Never shown in the QR code.
    id = db.Column(db.Integer, primary_key=True)

    # The company that owns this machine. Every lookup filters on it.
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.id"),
        nullable=False,
        index=True
    )

    # Random ID in the QR code URL. Set once and never changed.
    public_id = db.Column(
        db.String(16),
        unique=True,
        nullable=False,
        default=generate_public_id
    )

    # The only field a user types in.
    name = db.Column(db.String(100), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)