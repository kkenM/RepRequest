"""
Authentication routes for RepRequest.

Responsibilities:
- Register a company and its first administrator
- Authenticate users
- End authenticated sessions
- Reload users from Flask-Login sessions
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
from models import Company, User


# Authentication Blueprint
auth_bp = Blueprint(
    "auth",
    __name__
)


@login_manager.user_loader
def load_user(user_id):
    """
    Reload a user from the database using the ID stored
    in the authenticated Flask session.
    """

    return db.session.get(User, int(user_id))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """
    Register a new company and create its first
    company-administrator account.
    """

    if request.method == "GET":
        return render_template("auth/register.html")

    company_name = request.form["company_name"].strip()
    first_name = request.form["first_name"].strip()
    last_name = request.form["last_name"].strip()
    email = request.form["email"].strip().lower()
    password = request.form["password"]

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

    existing_user = User.query.filter_by(
        email=email
    ).first()

    if existing_user:
        return render_template(
            "auth/register.html",
            error="An account with that email already exists."
        )

    # Create the company first so its ID can be assigned
    # to the company's initial administrator.
    company = Company(
        name=company_name
    )

    db.session.add(company)
    db.session.flush()

    admin_user = User(
        company_id=company.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        role=User.ROLE_COMPANY_ADMIN
    )

    admin_user.set_password(password)

    db.session.add(admin_user)
    db.session.commit()

    return redirect(
        url_for("auth.login")
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """
    Authenticate an existing RepRequest user.
    """

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    if request.method == "POST":

        email = request.form["email"].strip().lower()
        password = request.form["password"]

        user = User.query.filter_by(
            email=email
        ).first()

        if user and user.check_password(password):

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


@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """
    End the current authenticated session.
    """

    logout_user()

    return redirect(
        url_for("auth.login")
    )