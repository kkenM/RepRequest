"""
MaintenanceLog model for RepRequest.

One row is written each time a technician completes a repair. Rows are
never edited, so a machine's log is an audit trail. Name, assignee and
last-maintenance date are copied in at that moment, so the history stays
accurate if a machine is renamed or an employee is later removed.
"""

from datetime import datetime

from app.extensions import db

CONDITION_EXCELLENT = "excellent"
CONDITION_GOOD = "good"
CONDITION_FAIR = "fair"
CONDITION_POOR = "poor"
CONDITION_REPLACE = "needs-replacement"

CONDITIONS = (
    CONDITION_EXCELLENT, CONDITION_GOOD, CONDITION_FAIR,
    CONDITION_POOR, CONDITION_REPLACE
)

CONDITION_LABELS = {
    CONDITION_EXCELLENT: "Excellent",
    CONDITION_GOOD: "Good",
    CONDITION_FAIR: "Fair",
    CONDITION_POOR: "Poor",
    CONDITION_REPLACE: "Needs Replacement"
}

MAX_LOCATION_LENGTH = 120
MAX_NOTES_LENGTH = 2000


class MaintenanceLog(db.Model):
    __tablename__ = "maintenance_log"

    id = db.Column(db.Integer, primary_key=True)

    # SECURITY: from the signed-in user, never from the form.
    company_id = db.Column(db.Integer, db.ForeignKey("company.id"), nullable=False)
    machine_id = db.Column(db.Integer, db.ForeignKey("machine.id"), nullable=False)

    # Not unique: a reopened request can be completed (and logged) again.
    repair_request_id = db.Column(
        db.Integer, db.ForeignKey("repair_request.id"), nullable=True, index=True
    )

    # Copied in when the log is written.
    machine_name = db.Column(db.String(120), nullable=False)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    assigned_to_name = db.Column(db.String(120), nullable=False, default="")
    last_maintenance_date = db.Column(db.Date, nullable=True)

    # Entered by the technician.
    condition = db.Column(db.String(20), nullable=False)
    location = db.Column(db.String(MAX_LOCATION_LENGTH), nullable=False, default="")
    notes = db.Column(db.Text, nullable=False)

    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    created_by_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    __table_args__ = (
        db.Index("ix_maintenance_log_machine", "company_id", "machine_id", "created_at"),
    )

    @property
    def condition_label(self):
        return CONDITION_LABELS.get(self.condition, self.condition)