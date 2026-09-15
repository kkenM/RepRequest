"""
General application routes for RepRequest.

Responsibilities:
- Application home page
- Authenticated user dashboard

Feature-specific functionality should live in its own Blueprint
rather than being added to this module.
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