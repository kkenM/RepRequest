from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

# database object
db = SQLAlchemy()

class Company(db.Model):
    # Unique identifier for each company
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # Company name
    name = db.Column(
        db.String(100),
        nullable=False
    )

    # Date and time creation
    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now()
    )

    # Relationship between company and users
    users = db.relationship(
        'User',
        backref='company',
        lazy=True
    )

class User(db.Model):
    # Unique ID for each user
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    # ID of user's parent company
    company_id = db.Column(
        db.Integer,
        db.ForeignKey('company.id'),
        nullable=False
    )

    # User first name
    first_name = db.Column(
        db.String(50),
        nullable=False
    )

    # User last name
    last_name = db.Column(
        db.String(50),
        nullable=False
    )

    # User email address
    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    # Secure password hash
    password_hash = db.Column(
        db.String(255),
        nullable=False
    )

    # User role in company
    role = db.Column(
        db.String(30),
        nullable=False
    )

    # Date and time user account creation
    created_at = db.Column(
        db.DateTime,
        default=datetime.now()
    )

    # Convert text to secure hash
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    # Check password matches
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)