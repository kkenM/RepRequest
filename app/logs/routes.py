"""
Maintenance-log HTTP routes for RepRequest.

Maintenance logs and per-machine history are designed but not yet implemented.
This Blueprint currently serves a placeholder page so that the navigation, the
authorisation rules and the URL structure are in place and can be tested before
the feature itself is built.

Business operations will be delegated to app.services.log_service.
"""

from flask import Blueprint, render_template

from app.authorization import role_required
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN


logs_bp = Blueprint(
    "logs",
    __name__,
    url_prefix="/maintenance-logs"
)


@logs_bp.route("/", strict_slashes=False)
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def index():
    """
    Display filed maintenance logs for the authenticated user's company.
    """

    return render_template(
        "logs/index.html"
    )
