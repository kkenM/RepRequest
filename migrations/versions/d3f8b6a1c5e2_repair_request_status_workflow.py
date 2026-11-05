"""repair request status workflow

Revision ID: d3f8b6a1c5e2
Revises: c7a1e2d4f9b3
Create Date: 2026-11-04 12:00:00.000000

Replaces the first set of statuses with: submitted, acknowledged,
assigned, in-progress, waiting-for-parts, completed, rejected, and
records who last changed a status and when.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3f8b6a1c5e2'
down_revision = 'c7a1e2d4f9b3'
branch_labels = None
depends_on = None


# old status -> new status. "down" has no equivalent, so it becomes
# in-progress rather than losing the request.
RENAMES = {
    'action-needed': 'submitted',
    'repair-complete': 'completed',
    'down': 'in-progress',
}


def upgrade():
    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('status_updated_at', sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column('status_updated_by_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(
            'fk_repair_request_status_updated_by',
            'user', ['status_updated_by_id'], ['id']
        )

    for old, new in RENAMES.items():
        op.execute(
            sa.text("UPDATE repair_request SET status = :new WHERE status = :old")
            .bindparams(new=new, old=old)
        )


def downgrade():
    # Map back as far as the old statuses allow. The new in-between
    # statuses all meant "still needs work" in the old scheme.
    op.execute("UPDATE repair_request SET status = 'repair-complete' WHERE status = 'completed'")
    op.execute(
        "UPDATE repair_request SET status = 'action-needed' "
        "WHERE status IN ('submitted', 'acknowledged', 'assigned', "
        "'waiting-for-parts', 'rejected')"
    )

    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.drop_constraint('fk_repair_request_status_updated_by', type_='foreignkey')
        batch_op.drop_column('status_updated_by_id')
        batch_op.drop_column('status_updated_at')
