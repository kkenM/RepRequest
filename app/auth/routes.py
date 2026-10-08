"""
Authentication HTTP routes for RepRequest.

Responsibilities include company registration, login, logout,
and authenticated-session behavior.

Business operations should be delegated to the service layer whenever
they are not specifically concerned with HTTP requests or sessions.
"""

from flask import (
    Blueprint,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app.extensions import login_manager
from app.services import (
    company_service,
    user_service
)
from app.services.exceptions import DuplicateEmailError


auth_bp = Blueprint(
    "auth",
    __name__
)


@login_manager.user_loader
def load_user(session_token):
    """
    Reload the authenticated user from the session token stored
    in the cookie. Returning None makes Flask-Login treat user
    as signed out.
    """

    return user_service.get_user_by_session_token(session_token)


@auth_bp.route(
    "/register",
    methods=["GET", "POST"]
)
def register():
    """
    Register a company and its first administrator.
    """

    if request.method == "GET":
        return render_template(
            "auth/register.html"
        )

    company_name = request.form["company_name"].strip()
    first_name = request.form["first_name"].strip()
    last_name = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]

    # HTTP/form validation belongs in the route.
    if (
        not company_name
        or not first_name
        or not last_name
        or not email
        or not password
    ):
        return render_template(
            "auth/register.html",
            error="All fields are required."
        )

    try:
        company_service.create_company_with_admin(
            company_name=company_name,
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password
        )

    except DuplicateEmailError:
        return render_template(
            "auth/register.html",
            error="An account with that email already exists."
        )

    return redirect(
        url_for("auth.login")
    )


@auth_bp.route(
    "/login",
    methods=["GET", "POST"]
)
def login():
    """
    Authenticate an existing RepRequest user.
    """

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = user_service.authenticate_user(
            email=email,
            password=password
        )

        if user:

            # Drop anything stored before login.
            session.clear()

            login_user(user)

            # Expire after PERMANENT_SESSION_LIFETIME.
            session.permanent = True

            return redirect(
                url_for("main.dashboard")
            )

        return render_template(
            "auth/login.html",
            error="Invalid email or password."
        )

    return render_template(
        "auth/login.html"
    )


@auth_bp.route(
    "/logout",
    methods=["POST"]
)
def logout():
    """
    End the current authenticated session.
    """

    logout_user()
    session.clear()

    return redirect(url_for("auth.login"))


@auth_bp.route(
    "/logout/all",
    methods=["POST"]
)
@login_required
def logout_all():
    """
    End the current user's session on all devices.
    """

    user_service.end_all_sessions(current_user)

    logout_user()
    session.clear()

    flash(
        "Signed out on all devices."
        "Success"
    )

    return redirect(
        url_for("auth.login")
    )