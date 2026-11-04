"""
Repair-request business logic for RepRequest.

Handles filing a repair request after a QR scan, the technician queue,
and notifying technicians about urgent faults.

Routes read the request and choose the response. This module must not
render templates, read request.form or redirect.
"""

from datetime import datetime

from flask import current_app
from sqlalchemy import case

from app.extensions import db
from app.models import RepairRequest, User
from app.models.repair_request import (
    CLOSED_STATUSES,
    STATUS_ACKNOWLEDGED,
    STATUS_ASSIGNED,
    MAX_DESCRIPTION_LENGTH,
    OPEN_STATUSES,
    SEVERITIES,
    SEVERITY_HIGH,
    STATUSES,
    STATUS_SUBMITTED
)
from app.roles import COMPANY_ADMIN, EMPLOYEE_TECHNICIAN
from app.services import email_service
from app.services.exceptions import (
    AssignmentNotAllowedError,
    InvalidRepairRequestError
)


def create_repair_request(reporter, machine, severity, description):
    """
    File a repair request for a machine, on behalf of the signed-in user.

    SECURITY: the company comes from the reporting user, and the machine
    must belong to that same company. Nothing company-related is taken
    from the submitted form.

    Raises InvalidRepairRequestError when the input is not acceptable.
    """

    if machine is None or machine.company_id != reporter.company_id:
        raise InvalidRepairRequestError("That machine could not be found.")

    if severity not in SEVERITIES:
        raise InvalidRepairRequestError("Choose a severity.")

    description = (description or "").strip()

    if not description:
        raise InvalidRepairRequestError("Describe the problem.")

    if len(description) > MAX_DESCRIPTION_LENGTH:
        raise InvalidRepairRequestError(
            f"Keep the description under {MAX_DESCRIPTION_LENGTH} characters."
        )

    repair_request = RepairRequest(
        company_id=reporter.company_id,
        machine_id=machine.id,
        reported_by_id=reporter.id,
        severity=severity,
        status=STATUS_SUBMITTED,
        description=description
    )

    db.session.add(repair_request)
    db.session.commit()

    # Only urgent faults send an email. The rest wait in the queue.
    if severity == SEVERITY_HIGH:
        notify_of_urgent_request(repair_request)

    return repair_request


def count_open_requests_for_machine(company_id, machine_id):
    """
    Number of unfinished requests already filed against a machine, so the
    scan page can tell the employee someone has already reported it.
    """

    return RepairRequest.query.filter(
        RepairRequest.company_id == company_id,
        RepairRequest.machine_id == machine_id,
        RepairRequest.status.in_(OPEN_STATUSES)
    ).count()


# Which requests the queue page shows.
VIEW_OPEN = "open"
VIEW_CLOSED = "closed"
VIEW_ALL = "all"
VIEW_MINE = "mine"
VIEWS = (VIEW_OPEN, VIEW_CLOSED, VIEW_ALL, VIEW_MINE)


def get_requests(company_id, view=VIEW_OPEN, user_id=None):
    """
    The company's requests for the technician queue, most severe first,
    then oldest first.

    view is "open" (still needs work), "closed" (completed or rejected),
    "mine" (open requests assigned to user_id) or "all". An unknown
    value is treated as "open".
    """

    severity_rank = case(
        {severity: rank for rank, severity in enumerate(SEVERITIES)},
        value=RepairRequest.severity,
        else_=len(SEVERITIES)
    )

    query = RepairRequest.query.filter(
        RepairRequest.company_id == company_id
    )

    if view == VIEW_CLOSED:
        query = query.filter(RepairRequest.status.in_(CLOSED_STATUSES))
    elif view == VIEW_MINE:
        query = query.filter(
            RepairRequest.status.in_(OPEN_STATUSES),
            RepairRequest.assigned_to_id == user_id
        )
    elif view != VIEW_ALL:
        query = query.filter(RepairRequest.status.in_(OPEN_STATUSES))

    return query.order_by(
        severity_rank,
        RepairRequest.created_at
    ).all()


def get_company_request(company_id, request_id):
    """
    One repair request, but only if it belongs to the company.
    """

    return RepairRequest.query.filter(
        RepairRequest.id == request_id,
        RepairRequest.company_id == company_id
    ).first()


def change_status(repair_request, new_status, user):
    """
    Move a request to a new status and record who did it and when.

    Any status can be chosen from any other, so a mistake can be undone.
    The caller must already have loaded the request through
    get_company_request() and checked that the user may change statuses.

    Raises InvalidRepairRequestError for a status that doesn't exist.
    """

    if new_status not in STATUSES:
        raise InvalidRepairRequestError("Choose a valid status.")

    if new_status == repair_request.status:
        return repair_request

    repair_request.status = new_status
    repair_request.status_updated_at = datetime.utcnow()
    repair_request.status_updated_by_id = user.id

    db.session.commit()

    return repair_request


def get_company_technicians(company_id):
    """
    The company's technician accounts, for the administrator's
    assignment dropdown.
    """

    return User.query.filter_by(
        company_id=company_id,
        role=EMPLOYEE_TECHNICIAN
    ).order_by(
        User.first_name,
        User.last_name
    ).all()


def get_company_user(company_id, user_id):
    """
    One user of any role, but only if they belong to the company.
    assign_request() decides whether that user may hold a request.
    """

    if user_id is None:
        return None

    return User.query.filter(
        User.id == user_id,
        User.company_id == company_id
    ).first()


def assign_request(repair_request, assignee, acting_user):
    """
    Assign a request to a technician, or unassign it (assignee=None).

    Rules:
      * An administrator may assign any technician in the company, or
        themselves, and may unassign anyone.
      * A technician may only assign themselves, and only to a request
        nobody holds yet. They may also unassign themselves.

    SECURITY: the assignee must belong to the same company as the
    request. The caller must already have loaded the request through
    get_company_request().

    Raises AssignmentNotAllowedError when the role doesn't permit it and
    InvalidRepairRequestError when the assignee can't be used.
    """

    is_admin = acting_user.role == COMPANY_ADMIN

    if assignee is None:
        # Unassigning: an administrator may release anyone's request,
        # a technician only their own.
        if not is_admin and repair_request.assigned_to_id != acting_user.id:
            raise AssignmentNotAllowedError()

        repair_request.assigned_to_id = None

        # Nobody holds it any more, so it can't still be "Assigned".
        if repair_request.status == STATUS_ASSIGNED:
            _set_status(repair_request, STATUS_ACKNOWLEDGED, acting_user)

        db.session.commit()
        return repair_request

    if assignee.company_id != repair_request.company_id:
        raise InvalidRepairRequestError("Choose a technician from your company.")

    eligible = (
        assignee.role == EMPLOYEE_TECHNICIAN
        or (assignee.role == COMPANY_ADMIN and assignee.id == acting_user.id)
    )

    if not eligible:
        raise InvalidRepairRequestError("Choose a technician.")

    if not is_admin:
        if assignee.id != acting_user.id:
            raise AssignmentNotAllowedError()

        held_by = repair_request.assigned_to_id

        if held_by not in (None, acting_user.id):
            raise AssignmentNotAllowedError()

    if repair_request.assigned_to_id == assignee.id:
        return repair_request

    repair_request.assigned_to_id = assignee.id

    # Taking on a request that nobody had picked up yet marks it Assigned.
    if repair_request.status in (STATUS_SUBMITTED, STATUS_ACKNOWLEDGED):
        _set_status(repair_request, STATUS_ASSIGNED, acting_user)

    db.session.commit()

    # Tell the technician when somebody else gave them the work.
    if assignee.id != acting_user.id:
        try:
            email_service.send_assignment_email(
                assignee, repair_request, acting_user
            )
        except OSError:
            current_app.logger.exception(
                "Could not email assignment notification to user %s",
                assignee.id
            )

    return repair_request


def release_user_from_requests(user):
    """
    Detach a user from repair requests before their account is deleted.

    The requests themselves are kept as history. Requests they held
    become unassigned, and drop back from Assigned to Acknowledged.
    """

    for repair in RepairRequest.query.filter_by(assigned_to_id=user.id).all():
        repair.assigned_to_id = None

        if repair.status == STATUS_ASSIGNED:
            repair.status = STATUS_ACKNOWLEDGED

    RepairRequest.query.filter_by(reported_by_id=user.id).update(
        {"reported_by_id": None}
    )
    RepairRequest.query.filter_by(status_updated_by_id=user.id).update(
        {"status_updated_by_id": None}
    )

    db.session.flush()


def _set_status(repair_request, status, user):
    repair_request.status = status
    repair_request.status_updated_at = datetime.utcnow()
    repair_request.status_updated_by_id = user.id


def notify_of_urgent_request(repair_request):
    """
    Email the company's technicians about a high-severity request.

    A small company may have no technician accounts, so the
    administrators are emailed in that case instead.

    A failed email never fails the request, which is already saved.
    """

    recipients = _company_users_with_role(
        repair_request.company_id,
        EMPLOYEE_TECHNICIAN
    ) or _company_users_with_role(
        repair_request.company_id,
        COMPANY_ADMIN
    )

    if not recipients:
        return

    for user in recipients:
        try:
            email_service.send_urgent_repair_email(user, repair_request)
        except OSError:
            current_app.logger.exception(
                "Could not email repair notification to user %s", user.id
            )


def _company_users_with_role(company_id, role):
    return User.query.filter_by(
        company_id=company_id,
        role=role
    ).all()
