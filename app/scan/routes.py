# Scan routes for the project

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.models.repair_request import (
    MAX_DESCRIPTION_LENGTH,
    SEVERITIES,
    SEVERITY_LABELS
)
from app.services import machine_service, repair_service


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/m/<public_id>")

# Shows which machine was scanned, with the form to report a problem
def machine(public_id):

    # If they aren't signed in, send them to login page. Login sends
    # them back here afterwards.
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))

    # Unknown ID and another company's machine give the same 404.
    machine = machine_service.get_company_machine_by_public_id(
        current_user.company_id,
        public_id
    )

    if machine is None:
        abort(404)

    return render_template(
        "scan/machine.html",
        machine=machine,
        open_count=repair_service.count_open_requests_for_machine(
            current_user.company_id,
            machine.id
        ),
        severities=[(value, SEVERITY_LABELS[value]) for value in SEVERITIES],
        max_description=MAX_DESCRIPTION_LENGTH,
        error=None,
        selected_severity="",
        description=""
    )
