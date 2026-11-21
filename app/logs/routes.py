"""
Maintenance-log HTTP routes for RepRequest.

Technicians and administrators complete a repair by filling out a
maintenance log, and read each machine's log history here.

Business operations are delegated to app.services.log_service.
"""

from flask import abort, flash, redirect, render_template, request, url_for
from flask import Blueprint
from flask_login import current_user

from app.authorization import role_required
from app.models.maintenance_log import CONDITIONS, CONDITION_LABELS
from app.models.repair_request import CLOSED_STATUSES
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN
from app.services import log_service, repair_service
from app.services.exceptions import InvalidMaintenanceLogError


logs_bp = Blueprint(
    "logs",
    __name__,
    url_prefix="/maintenance-logs"
)

CONDITION_OPTIONS = [(c, CONDITION_LABELS[c]) for c in CONDITIONS]


@logs_bp.route("/", strict_slashes=False)
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def index():
    """
    List the company's machines, each linking to its maintenance log.
    """

    summaries = log_service.get_machine_summaries(current_user.company_id)

    return render_template("logs/index.html", summaries=summaries)


@logs_bp.route("/machines/<int:machine_id>")
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def machine_log(machine_id):
    """
    One machine's maintenance log, newest entry first.
    """

    machine = log_service.get_company_machine(
        current_user.company_id, machine_id
    )

    if machine is None:
        abort(404)

    logs = log_service.get_logs_for_machine(
        current_user.company_id, machine.id
    )

    return render_template("logs/machine_log.html", machine=machine, logs=logs)


@logs_bp.route("/complete/<int:request_id>", methods=["GET", "POST"])
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def complete_repair(request_id):
    """
    Completing a repair means filling out its maintenance log.
    """

    repair_request = repair_service.get_company_request(
        current_user.company_id, request_id
    )

    if repair_request is None:
        abort(404)

    if repair_request.status in CLOSED_STATUSES:
        flash("This request is already closed.", "error")
        return redirect(url_for(
            "logs.machine_log", machine_id=repair_request.machine_id
        ))

    prefill = log_service.build_prefill(repair_request)

    if request.method == "POST":
        try:
            log = log_service.complete_repair_with_log(
                repair_request, current_user,
                condition=request.form.get("condition"),
                location=request.form.get("location"),
                notes=request.form.get("notes"),
            )
        except InvalidMaintenanceLogError as error:
            flash(str(error), "error")
            return render_template(
                "logs/log_form.html", prefill=prefill,
                conditions=CONDITION_OPTIONS, repair_request=repair_request
            ), 400

        flash("Repair completed and maintenance log saved.", "success")
        return redirect(url_for("logs.machine_log", machine_id=log.machine_id))

    return render_template(
        "logs/log_form.html", prefill=prefill,
        conditions=CONDITION_OPTIONS, repair_request=repair_request
    )
