"""
Company-related business logic for RepRequest.

This module manages operations that involve Company entities
and their associated account setup.
"""

from app.roles import COMPANY_ADMIN
from app.extensions import db
from app.models import Company, User
from app.services.exceptions import DuplicateEmailError
from app.services.user_service import (
    get_user_by_email,
    normalize_email
)


def create_company_with_admin(
    company_name,
    first_name,
    last_name,
    email,
    password
):
    """
    Create a new Company and its first company administrator.

    The Company must be created first so its generated ID can
    be assigned to the administrator account.
    """

    email = normalize_email(email)

    if get_user_by_email(email):
        raise DuplicateEmailError()

    company = Company(
        name=company_name
    )

    db.session.add(company)

    # Generate the Company ID before the transaction is committed.
    db.session.flush()

    admin_user = User(
        company_id=company.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=COMPANY_ADMIN
    )

    admin_user.set_password(password)

    db.session.add(admin_user)
    db.session.commit()

    return company, admin_user