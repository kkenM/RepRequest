from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# database object
db = SQLAlchemy()

class Company(db.Model):
    # Unique identifier for each company
    id = db.Column(db.Integer, primary_key=True)

    # Company name
    name = db.Column(db.String(100), nullable=False)

    # Date and time creation
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now())

