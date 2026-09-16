"""
RepRequest database models.

Import models from this package rather than directly from
their individual files when possible.

Example:

    from app.models import Company, User
"""

from app.models.company import Company
from app.models.user import User


__all__ = [
    "Company",
    "User"
]