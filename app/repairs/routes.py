"""
Repair-request HTTP routes for RepRequest.

An employee scans a machine's QR code, which opens /m/<public_id>
(see app/scan). That page posts its form here. Technicians and
administrators read the repair queue.

Business operations are delegated to app.services.repair_service.
"""

from flask import (
    Blueprint,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for
)
from flask_login import current_user

from app.authorization import role_required
from app.models.repair_request import (
    MAX_DESCRIPTION_LENGTH,
    SEVERITIES,
    SEVERITY_LABELS,
    STATUSES,
    STATUS_LABELS
)
from app.roles import COMPANY_ADMIN, EMPLOYEE_CREW, EMPLOYEE_TECHNICIAN
from app.services import machine_service, repair_service
from app.services.exceptions import (
    AssignmentNotAllowedError,
    InvalidRepairRequestError
)


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

    ?view=open (default), closed or all chooses which requests to list.
    """

    view = request.args.get("view", repair_service.VIEW_OPEN)

    if view not in repair_service.VIEWS:
        view = repair_service.VIEW_OPEN

    is_admin = current_user.role == COMPANY_ADMIN

    # Only an administrator picks other people. They may also take a
    # request themselves.
    assignee_choices = []

    if is_admin:
        assignee_choices = repair_service.get_company_technicians(
            current_user.company_id
        )

    return render_template(
        "repairs/index.html",
        repair_requests=repair_service.get_requests(
            current_user.company_id,
            view,
            user_id=current_user.id
        ),
        view=view,
        status_options=[(value, STATUS_LABELS[value]) for value in STATUSES],
        is_admin=is_admin,
        assignee_choices=assignee_choices
    )


@repairs_bp.route("/<int:request_id>/status", methods=["POST"])
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def change_status(request_id):
    """
    Let an administrator or technician change a request's status.

    The request is looked up inside the signed-in user's company, so
    another company's request id is an ordinary 404.
    """

    repair_request = repair_service.get_company_request(
        current_user.company_id,
        request_id
    )

    if repair_request is None:
        abort(404)

    try:
        repair_service.change_status(
            repair_request,
            request.form.get("status", ""),
            current_user
        )

    except InvalidRepairRequestError as error:
        flash(str(error), "error")

    else:
        flash(
            f"{repair_request.machine.name} is now "
            f"{repair_request.status_label}.",
            "success"
        )

    # Stay on the same tab of the queue.
    view = request.form.get("view", repair_service.VIEW_OPEN)

    if view not in repair_service.VIEWS:
        view = repair_service.VIEW_OPEN

    return redirect(url_for("repairs.index", view=view))


@repairs_bp.route("/<int:request_id>/assign", methods=["POST"])
@role_required(COMPANY_ADMIN, EMPLOYEE_TECHNICIAN)
def assign(request_id):
    """
    Assign a request to a technician, or unassign it.

    An administrator may choose any technician in the company. A
    technician may only take an unassigned request for themselves, or
    release one they hold. The service enforces this, so a hand-edited
    form can't go further than the buttons allow.
    """

    repair_request = repair_service.get_company_request(
        current_user.company_id,
        request_id
    )

    if repair_request is None:
        abort(404)

    assignee = None
    raw_id = request.form.get("assignee_id", "").strip()

    if raw_id:
        # SECURITY: the user is looked up inside the company, so another
        # company's user id behaves like an unknown one.
        assignee = repair_service.get_company_user(
            current_user.company_id,
            int(raw_id) if raw_id.isdigit() else None
        )

        if assignee is None:
            flash("Choose a technician from your company.", "error")
            return _back_to_queue()

    try:
        repair_service.assign_request(
            repair_request,
            assignee,
            current_user
        )

    except AssignmentNotAllowedError:
        abort(403)

    except InvalidRepairRequestError as error:
        flash(str(error), "error")

    else:
        if assignee is None:
            flash(f"{repair_request.machine.name} is now unassigned.", "success")
        else:
            flash(
                f"{repair_request.machine.name} is assigned to "
                f"{assignee.first_name} {assignee.last_name}.",
                "success"
            )

    return _back_to_queue()


def _back_to_queue():
    """Return to the same tab of the queue the form was submitted from."""

    view = request.form.get("view", repair_service.VIEW_OPEN)

    if view not in repair_service.VIEWS:
        view = repair_service.VIEW_OPEN

    return redirect(url_for("repairs.index", view=view))


@repairs_bp.route("/report/<public_id>", methods=["POST"])
@role_required(COMPANY_ADMIN, EMPLOYEE_CREW, EMPLOYEE_TECHNICIAN)
def submit(public_id):
    """
    File a repair request for the machine whose QR code was scanned.

    The machine is looked up inside the signed-in user's company, so a
    QR code from another company is an ordinary 404.
    """

    machine = machine_service.get_company_machine_by_public_id(
        current_user.company_id,
        public_id
    )

    if machine is None:
        abort(404)

    severity = request.form.get("severity", "")
    description = request.form.get("description", "")

    try:
        repair_service.create_repair_request(
            reporter=current_user,
            machine=machine,
            severity=severity,
            description=description
        )

    except InvalidRepairRequestError as error:

        # Show the form again with what the employee already typed.
        return render_template(
            "scan/machine.html",
            machine=machine,
            open_count=repair_service.count_open_requests_for_machine(
                current_user.company_id,
                machine.id
            ),
            severities=[
                (value, SEVERITY_LABELS[value]) for value in SEVERITIES
            ],
            max_description=MAX_DESCRIPTION_LENGTH,
            error=str(error),
            selected_severity=severity,
            description=description
        ), 400

    flash("Repair request sent. A technician has been notified.", "success")

    return redirect(url_for("scan.machine", public_id=public_id))
