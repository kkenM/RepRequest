"""
Authentication routes for RepRequest.

Responsibilities:
- Register a company and its first administrator
- Authenticate users
- End authenticated sessions
- Reload users from Flask-Login sessions

Business logic belongs in the service layer rather than here.
"""

from flask import (
    Blueprint,
    redirect,
    render_template,
    request,
    url_for
)

from flask_login import (
    current_user,
    login_required,
    login_user,
    logout_user
)

from app.extensions import db, login_manager
from app.models import User
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
def load_user(user_id):
    """
    Reload the authenticated user using the ID stored
    in the Flask session.
    """

    return db.session.get(
        User,
        int(user_id)
    )


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
            login_user(user)

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
@login_required
def logout():
    """
    End the current authenticated session.
    """

    logout_user()

    return redirect(
        url_for("auth.login")
    )