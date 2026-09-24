"""
Machine-registry HTTP routes for RepRequest.

The machine registry, QR tokens and machine history are designed but not yet
implemented. This Blueprint currently serves a placeholder page so that the
navigation, the authorisation rules and the URL structure are in place and can
be tested before the feature itself is built.

Business operations will be delegated to app.services.machine_service.
"""

from flask import Blueprint, render_template

from app.authorization import role_required
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN


machines_bp = Blueprint(
    "machines",
    __name__,
    url_prefix="/machines"
)


@machines_bp.route("/", strict_slashes=False)
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def index():
    """
    Display the machine registry for the authenticated user's company.
    """

    return render_template(
        "machines/index.html"
    )
