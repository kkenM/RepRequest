"""
Repair-request HTTP routes for RepRequest.

Repair-request submission and the technician repair queue are designed but not
yet implemented. This Blueprint currently serves a placeholder page so that the
navigation, the authorisation rules and the URL structure are in place and can
be tested before the feature itself is built.

Business operations will be delegated to app.services.repair_service.
"""

from flask import Blueprint, render_template

from app.authorization import role_required
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN


repairs_bp = Blueprint(
    "repairs",
    __name__,
    url_prefix="/repairs"
)


@repairs_bp.route("/", strict_slashes=False)
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def index():
    """
    Display the repair queue for the authenticated user's company.
    """

    return render_template(
        "repairs/index.html"
    )
