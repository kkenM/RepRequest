"""
General application routes for RepRequest.

This Blueprint contains shared application pages such as the home page
and authenticated user dashboard.

Feature-specific behavior should live in its own Blueprint.
"""

from flask import Blueprint, render_template
from flask_login import login_required


# Blueprint for general application pages
main_bp = Blueprint(
    "main",
    __name__
)


@main_bp.route("/")
def home():
    """
    Display the RepRequest home page.
    """

    return "RepRequest is running!"


@main_bp.route("/dashboard")
@login_required
def dashboard():
    """
    Display the dashboard for the authenticated user.
    """

    return render_template("main/dashboard.html")