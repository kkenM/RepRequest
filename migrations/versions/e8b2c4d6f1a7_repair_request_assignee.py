"""repair request assignee

Revision ID: e8b2c4d6f1a7
Revises: d3f8b6a1c5e2
Create Date: 2026-11-04 15:00:00.000000

Adds the technician (or administrator) a repair request is assigned to.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8b2c4d6f1a7'
down_revision = 'd3f8b6a1c5e2'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.add_column(sa.Column('assigned_to_id', sa.Integer(), nullable=True))
        batch_op.create_index(batch_op.f('ix_repair_request_assigned_to_id'), ['assigned_to_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_repair_request_assigned_to',
            'user', ['assigned_to_id'], ['id']
        )


def downgrade():
    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.drop_constraint('fk_repair_request_assigned_to', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_repair_request_assigned_to_id'))
        batch_op.drop_column('assigned_to_id')
