"""
User-related business logic for RepRequest.

This module handles account operations that should not be tied
directly to Flask routes.

Responsibilities include:
- Looking up users
- Authenticating users
- Retrieving company employees
- Creating employees
- Updating employees
- Deleting employees
"""

from app.roles import EMPLOYEE_ROLES
from app.extensions import db
from app.models import User
from app.services.exceptions import (
    DuplicateEmailError,
    InvalidEmployeeRoleError
)


def normalize_email(email):
    """
    Normalize an email address before storing or searching for it.
    """

    return email.strip().lower()


def get_user_by_email(email):
    """
    Retrieve a user by normalized email address.
    """

    email = normalize_email(email)

    return User.query.filter_by(
        email=email
    ).first()


def authenticate_user(email, password):
    """
    Return the matching User when credentials are valid.

    Return None when the email or password is incorrect.
    """

    user = get_user_by_email(email)

    if user and user.check_password(password):
        return user

    return None


def get_company_employees(company_id):
    """
    Return employee accounts belonging to one company.

    Company administrator accounts are intentionally excluded.
    """

    return User.query.filter(
        User.company_id == company_id,
        User.role.in_(EMPLOYEE_ROLES)
    ).order_by(
        User.last_name,
        User.first_name
    ).all()


def get_company_employee(company_id, employee_id):
    """
    Retrieve one employee only when they belong to the
    specified company.

    Returns None when the employee does not exist, belongs
    to another company, or is not an employee account.
    """

    return User.query.filter(
        User.id == employee_id,
        User.company_id == company_id,
        User.role.in_(EMPLOYEE_ROLES)
    ).first()


def create_employee(
    company_id,
    first_name,
    last_name,
    email,
    password,
    role
):
    """
    Create an employee under the specified company.

    company_id must come from the authenticated administrator,
    never directly from submitted form data.
    """

    email = normalize_email(email)

    if role not in EMPLOYEE_ROLES:
        raise InvalidEmployeeRoleError()

    if get_user_by_email(email):
        raise DuplicateEmailError()

    employee = User(
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=role
    )

    employee.set_password(password)

    db.session.add(employee)
    db.session.commit()

    return employee


def update_employee(
    employee,
    first_name,
    last_name,
    email,
    role
):
    """
    Update an existing employee account.
    """

    email = normalize_email(email)

    if role not in EMPLOYEE_ROLES:
        raise InvalidEmployeeRoleError()

    existing_user = User.query.filter(
        User.email == email,
        User.id != employee.id
    ).first()

    if existing_user:
        raise DuplicateEmailError()

    employee.first_name = first_name
    employee.last_name = last_name
    employee.email = email
    employee.role = role

    db.session.commit()

    return employee


def delete_employee(employee):
    """
    Permanently delete an employee account.
    """

    db.session.delete(employee)
    db.session.commit()