"""
User-related business logic for RepRequest.

Routes should call these functions instead of directly implementing
user database operations.

This module must not render templates, access request.form, or perform
HTTP redirects.
"""

import hashlib
import re
import secrets
import unicodedata

from flask import current_app
from itsdangerous import BadSignature, URLSafeTimedSerializer

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


def get_user_by_username(username):
    """
    Retrieve a user by username (case-insensitive).
    """

    return User.query.filter_by(
        username=username.strip().lower()
    ).first()


def get_user_by_login(identifier):
    """
    Find a user by email when the value contains "@",
    otherwise by username.
    """

    if "@" in identifier:
        return get_user_by_email(identifier)

    return get_user_by_username(identifier)


def authenticate_user(identifier, password):
    """
    Return the matching User when the username or email and
    the password are valid. Return None otherwise.
    """

    user = get_user_by_login(identifier)

    if user and user.check_password(password):
        return user

    return None


def _ascii_letters(text):
    """
    "José O'Brien" -> "joseobrien": accents removed, letters only.
    """

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode()

    return re.sub(r"[^a-z]", "", text.lower())


def generate_username(first_name, last_name):
    """
    First initial + last name + a random number, e.g. "jdoe42".

    Tries two digits (10-99) first, then three digits if a
    name is very common.
    """

    first = _ascii_letters(first_name)
    last = _ascii_letters(last_name)
    base = (first[:1] + last)[:20] or "user"

    for low, high, attempts in ((10, 99, 30), (100, 999, 100)):
        for _ in range(attempts):
            number = low + secrets.randbelow(high - low + 1)
            candidate = f"{base}{number}"

            if not get_user_by_username(candidate):
                return candidate

    raise RuntimeError("Could not generate a unique username.")


def generate_temporary_password():
    """
    Return 16 random URL-safe characters.
    """

    return secrets.token_urlsafe(12)


def get_user_by_session_token(session_token):
    """
    Return the user that owns a session token, or None
    when the token was rotated or the account deleted.
    """

    if not session_token:
        return None

    return User.query.filter_by(session_token=session_token).first()


def end_all_sessions(user):
    """
    Sign a user out of every device.
    """

    user.rotate_session_token()

    db.session.commit()


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
    role,
    username=None,
    must_change_password=False
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
        role=role,
        username=username,
        must_change_password=must_change_password
    )

    employee.set_password(password)

    db.session.add(employee)
    db.session.commit()

    return employee


def create_employee_with_temporary_password(
    company_id,
    first_name,
    last_name,
    email,
    role
):
    """
    Create an employee with a generated username and temporary
    password.

    Returns (employee, temporary_password) so the route can email
    the password. Only its hash is stored.
    """

    temporary_password = generate_temporary_password()

    employee = create_employee(
        company_id=company_id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        password=temporary_password,
        role=role,
        username=generate_username(first_name, last_name),
        must_change_password=True
    )

    return employee, temporary_password


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


def change_password(user, new_password):
    """
    Set a new password and clear the temporary-password flag.

    set_password() also rotates the session token, which signs
    the user out on every device and invalidates any unused
    reset links.
    """

    user.set_password(new_password)
    user.must_change_password = False

    db.session.commit()


def _reset_serializer():
    return URLSafeTimedSerializer(
        current_app.config["SECRET_KEY"],
        salt="password-reset"
    )


def _session_fingerprint(user):
    """
    A short hash of the session token. It changes whenever the
    password changes, which makes each reset link single-use.
    """

    return hashlib.sha256(
        user.session_token.encode()
    ).hexdigest()[:16]


def make_password_reset_token(user):
    return _reset_serializer().dumps(
        {"id": user.id, "fp": _session_fingerprint(user)}
    )


def get_user_from_reset_token(token, max_age_seconds=3600):
    """
    Return the user for a valid, unexpired, unused reset token,
    or None.
    """

    try:
        data = _reset_serializer().loads(
            token,
            max_age=max_age_seconds
        )
    except BadSignature:  # also covers expired tokens
        return None

    user = db.session.get(User, data.get("id"))

    if user is None or data.get("fp") != _session_fingerprint(user):
        return None

    return user