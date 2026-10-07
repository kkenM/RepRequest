"""
General application routes for RepRequest.

This Blueprint contains shared application pages such as the public home page
and the authenticated user dashboard.

Feature-specific behavior should live in its own Blueprint.
"""

from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user, login_required


# Blueprint for general application pages
main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
def home():
    """
    Display the public RepRequest home page.

    Authenticated users are sent straight to their dashboard so that the
    marketing page is only shown to visitors who are not signed in.
    """

    if current_user.is_authenticated:
        return redirect(
            url_for("main.dashboard")
        )

    return render_template("main/home.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Display the dashboard for the authenticated user.
    """

    return render_template("main/dashboard.html")
