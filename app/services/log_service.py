"""
Maintenance-log business logic for RepRequest.

A log is written when a technician completes a repair. Routes read the
request and choose the response. This module must not render templates,
read request.form or redirect.
"""

from app.extensions import db
from app.models import Machine, MaintenanceLog
from app.models.maintenance_log import (
    CONDITIONS, MAX_LOCATION_LENGTH, MAX_NOTES_LENGTH
)
from app.models.repair_request import CLOSED_STATUSES
from app.services import repair_service
from app.services.exceptions import InvalidMaintenanceLogError


def _full_name(user):
    # CHECK: use your User's own display-name property if it has one.
    return f"{user.first_name} {user.last_name}".strip() if user else ""


def get_company_machine(company_id, machine_id):
    """One machine, but only if it belongs to the company."""
    return Machine.query.filter(
        Machine.id == machine_id,
        Machine.company_id == company_id
    ).first()


def get_logs_for_machine(company_id, machine_id):
    """
    A machine's logs, newest first. Newest-first is what puts a new
    entry in the row above the previous ones.
    """
    return MaintenanceLog.query.filter(
        MaintenanceLog.company_id == company_id,
        MaintenanceLog.machine_id == machine_id
    ).order_by(
        MaintenanceLog.created_at.desc(),
        MaintenanceLog.id.desc()
    ).all()


def build_prefill(repair_request):
    """
    The values the form shows. The same function runs again on submit,
    so nothing in the browser can change them.
    """
    machine = repair_request.machine
    logs = get_logs_for_machine(repair_request.company_id, machine.id)
    previous = logs[0] if logs else None
    assignee = repair_request.assigned_to

    return {
        "machine_name": machine.name,   # CHECK: Machine field names
        "machine_id": machine.id,       # CHECK: swap if you have a human-readable code
        "assigned_to_id": assignee.id if assignee else None,
        "assigned_to_name": _full_name(assignee),
        "last_maintenance_date": previous.created_at.date() if previous else None,
        "location": previous.location if previous
                    else (getattr(machine, "location", "") or ""),
    }


def complete_repair_with_log(repair_request, technician, condition, location, notes):
    """
    Write the maintenance log and mark the request Completed in ONE commit.

    SECURITY: company, machine and assignee come from the stored request,
    not from the form. The caller must already have loaded the request
    through repair_service.get_company_request().

    Raises InvalidMaintenanceLogError when the input is not acceptable.
    """

    if repair_request.status in CLOSED_STATUSES:
        raise InvalidMaintenanceLogError("This request is already closed.")

    if condition not in CONDITIONS:
        raise InvalidMaintenanceLogError("Choose a condition.")

    location = (location or "").strip()
    notes = (notes or "").strip()

    if len(location) > MAX_LOCATION_LENGTH:
        raise InvalidMaintenanceLogError(
            f"Keep the location under {MAX_LOCATION_LENGTH} characters."
        )

    if not notes:
        raise InvalidMaintenanceLogError("Add repair notes.")

    if len(notes) > MAX_NOTES_LENGTH:
        raise InvalidMaintenanceLogError(
            f"Keep the notes under {MAX_NOTES_LENGTH} characters."
        )

    prefill = build_prefill(repair_request)

    log = MaintenanceLog(
        company_id=repair_request.company_id,
        machine_id=prefill["machine_id"],
        repair_request_id=repair_request.id,
        machine_name=prefill["machine_name"],
        assigned_to_id=prefill["assigned_to_id"],
        assigned_to_name=prefill["assigned_to_name"],
        last_maintenance_date=prefill["last_maintenance_date"],
        condition=condition,
        location=location,
        notes=notes,
        created_by_id=technician.id,
    )

    repair_service.apply_completed_status(repair_request, technician)
    db.session.add(log)
    db.session.commit()

    return log


def get_machine_summaries(company_id):
    """
    Every company machine with its newest log and its log count, for the
    index page.
    """

    machines = Machine.query.filter(
        Machine.company_id == company_id
    ).order_by(Machine.name).all()      # CHECK: Machine.name

    latest = {}
    counts = {}

    for log in MaintenanceLog.query.filter(
        MaintenanceLog.company_id == company_id
    ).order_by(
        MaintenanceLog.created_at.desc(),
        MaintenanceLog.id.desc()
    ).all():
        counts[log.machine_id] = counts.get(log.machine_id, 0) + 1
        latest.setdefault(log.machine_id, log)   # first seen = newest

    return [
        {"machine": m, "latest": latest.get(m.id), "count": counts.get(m.id, 0)}
        for m in machines
    ]