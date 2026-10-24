# Scan routes for the project

from flask import Blueprint, abort, redirect, render_template, request, url_for
from flask_login import current_user

from app.services import machine_service


scan_bp = Blueprint("scan", __name__)


@scan_bp.route("/m/<public_id>")

# Shows which machine was scanned
def machine(public_id):

    # If they aren't signed in, send them to login page
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.path))

    machine = machine_service.get_machine_by_public_id(public_id)

    # Unknown ID and another company's machine give the same 404.
    if machine is None or machine.company_id != current_user.company_id:
        abort(404)

    # Show machine's name and details
    return render_template("scan/machine.html", machine=machine)