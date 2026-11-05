"""
RepairRequest model for RepRequest.

A repair request is filed by a signed-in employee after scanning a
machine's QR code. Technicians work the queue of open requests.
"""

from datetime import datetime

from app.extensions import db


# Severity values, from the form the employee fills in.
SEVERITY_LOW = "low"
SEVERITY_MEDIUM = "medium"
SEVERITY_HIGH = "high"

# Highest urgency first. The queue sorts by this order.
SEVERITIES = (SEVERITY_HIGH, SEVERITY_MEDIUM, SEVERITY_LOW)

SEVERITY_LABELS = {
    SEVERITY_HIGH: "High",
    SEVERITY_MEDIUM: "Medium",
    SEVERITY_LOW: "Low"
}

# Statuses, in the order a request normally moves through them.
STATUS_SUBMITTED = "submitted"
STATUS_ACKNOWLEDGED = "acknowledged"
STATUS_ASSIGNED = "assigned"
STATUS_IN_PROGRESS = "in-progress"
STATUS_WAITING_FOR_PARTS = "waiting-for-parts"
STATUS_COMPLETED = "completed"
STATUS_REJECTED = "rejected"

STATUSES = (
    STATUS_SUBMITTED,
    STATUS_ACKNOWLEDGED,
    STATUS_ASSIGNED,
    STATUS_IN_PROGRESS,
    STATUS_WAITING_FOR_PARTS,
    STATUS_COMPLETED,
    STATUS_REJECTED
)

STATUS_LABELS = {
    STATUS_SUBMITTED: "Submitted",
    STATUS_ACKNOWLEDGED: "Acknowledged",
    STATUS_ASSIGNED: "Assigned",
    STATUS_IN_PROGRESS: "In Progress",
    STATUS_WAITING_FOR_PARTS: "Waiting for Parts",
    STATUS_COMPLETED: "Completed",
    STATUS_REJECTED: "Rejected"
}

# Finished requests. Everything else still needs a technician.
CLOSED_STATUSES = (STATUS_COMPLETED, STATUS_REJECTED)

OPEN_STATUSES = tuple(
    status for status in STATUSES if status not in CLOSED_STATUSES
)

MAX_DESCRIPTION_LENGTH = 2000


class RepairRequest(db.Model):
    """
    One reported fault on one machine.
    """

    __tablename__ = "repair_request"

    id = db.Column(db.Integer, primary_key=True)

    # SECURITY: copied from the reporting user's session, never from
    # the submitted form.
    company_id = db.Column(
        db.Integer,
        db.ForeignKey("company.id"),
        nullable=False
    )

    machine_id = db.Column(
        db.Integer,
        db.ForeignKey("machine.id"),
        nullable=False,
        index=True
    )

    # Nullable so the request survives if the employee is removed.
    reported_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    severity = db.Column(db.String(10), nullable=False)

    status = db.Column(
        db.String(20),
        nullable=False,
        default=STATUS_SUBMITTED
    )

    description = db.Column(db.Text, nullable=False)

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow
    )

    # Who last changed the status, and when. Empty until someone does.
    status_updated_at = db.Column(db.DateTime, nullable=True)

    status_updated_by_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True
    )

    # The technician (or administrator) working on this request.
    assigned_to_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=True,
        index=True
    )

    machine = db.relationship("Machine")

    reported_by = db.relationship(
        "User",
        foreign_keys=[reported_by_id]
    )

    status_updated_by = db.relationship(
        "User",
        foreign_keys=[status_updated_by_id]
    )

    assigned_to = db.relationship(
        "User",
        foreign_keys=[assigned_to_id]
    )

    __table_args__ = (
        db.Index(
            "ix_repair_request_queue",
            "company_id",
            "status",
            "severity"
        ),
    )

    @property
    def severity_label(self):
        return SEVERITY_LABELS.get(self.severity, self.severity)

    @property
    def status_label(self):
        return STATUS_LABELS.get(self.status, self.status)
