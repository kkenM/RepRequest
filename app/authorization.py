"""
Authorization helpers for RepRequest.

Authentication determines who a user is.
Authorization determines what that user is allowed to access.

Route-access rules should be defined here rather than inside
individual feature Blueprints.
"""

from functools import wraps

from flask import abort
from flask_login import (
    current_user,
    login_required
)

from app.roles import COMPANY_ADMIN


def role_required(*allowed_roles):
    """
    Restrict a route to authenticated users whose role
    appears in allowed_roles.

    Unauthenticated users are handled by Flask-Login.
    Authenticated users with insufficient permission receive
    HTTP 403 Forbidden.
    """

    def decorator(view_function):

        @wraps(view_function)
        @login_required
        def wrapped_view(*args, **kwargs):

            if current_user.role not in allowed_roles:
                abort(403)

            return view_function(
                *args,
                **kwargs
            )

        return wrapped_view

    return decorator


def company_admin_required(view_function):
    """
    Restrict a route to company administrators.
    """

    return role_required(
        COMPANY_ADMIN
    )(view_function)