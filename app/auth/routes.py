"""
Authentication HTTP routes for RepRequest.

Responsibilities include company registration, login, logout,
and authenticated-session behavior.

Business operations should be delegated to the service layer whenever
they are not specifically concerned with HTTP requests or sessions.
"""

from flask import (
    Blueprint,
    current_app,
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
    email_service,
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

        identifier = request.form["login"]
        password = request.form["password"]

        user = user_service.authenticate_user(
            identifier=identifier,
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
            error="Invalid username, email or password."
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


@auth_bp.before_app_request
def require_password_change():
    """
    Send users still on a temporary password to the
    change-password page before they can use anything else.

    before_app_request runs before every request in the app,
    not only requests to this Blueprint.
    """

    allowed = {
        "auth.change_password",
        "auth.logout",
        "static"
    }

    if (
        current_user.is_authenticated
        and current_user.must_change_password
        and request.endpoint not in allowed
    ):
        return redirect(
            url_for("auth.change_password")
        )


@auth_bp.route(
    "/account/password",
    methods=["GET", "POST"]
)
@login_required
def change_password():
    """
    Let a signed-in user replace their password.
    """

    if request.method == "GET":
        return render_template(
            "auth/change_password.html"
        )

    current = request.form["current_password"]
    new = request.form["new_password"]
    confirm = request.form["confirm_password"]

    if not current_user.check_password(current):
        error = "Your current password is incorrect."
    elif len(new) < 8:
        error = "Use at least 8 characters."
    elif new != confirm:
        error = "The new passwords don't match."
    else:
        error = None

    if error:
        return render_template(
            "auth/change_password.html",
            error=error
        )

    user = current_user._get_current_object()

    user_service.change_password(user, new)

    # Changing the password rotated the session token, which
    # signed this browser out too. Sign it back in.
    login_user(user)
    session.permanent = True

    flash(
        "Your password has been updated.",
        "success"
    )

    return redirect(
        url_for("main.dashboard")
    )


@auth_bp.route(
    "/forgot-password",
    methods=["GET", "POST"]
)
def forgot_password():
    """
    Email a one-time reset link to the account's personal email.
    """

    if request.method == "GET":
        return render_template(
            "auth/forgot_password.html"
        )

    user = user_service.get_user_by_login(
        request.form["login"]
    )

    if user:
        token = user_service.make_password_reset_token(user)

        reset_url = url_for(
            "auth.reset_password",
            token=token,
            _external=True
        )

        try:
            email_service.send_password_reset_email(
                user,
                reset_url
            )
        except OSError:
            current_app.logger.exception(
                "Password reset email failed"
            )

    # SECURITY:
    # The same message whether or not the account exists, so this
    # page can't be used to discover usernames or emails.
    flash(
        "If that account exists, a reset link has been emailed to it.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )


@auth_bp.route(
    "/reset-password/<token>",
    methods=["GET", "POST"]
)
def reset_password(token):
    """
    Set a new password from an emailed reset link.
    """

    user = user_service.get_user_from_reset_token(token)

    if user is None:
        flash(
            "That reset link is invalid or has expired.",
            "error"
        )

        return redirect(
            url_for("auth.forgot_password")
        )

    if request.method == "GET":
        return render_template(
            "auth/reset_password.html"
        )

    new = request.form["new_password"]
    confirm = request.form["confirm_password"]

    if len(new) < 8:
        return render_template(
            "auth/reset_password.html",
            error="Use at least 8 characters."
        )

    if new != confirm:
        return render_template(
            "auth/reset_password.html",
            error="The passwords don't match."
        )

    user_service.change_password(user, new)

    flash(
        "Password updated. Sign in with your new password.",
        "success"
    )

    return redirect(
        url_for("auth.login")
    )