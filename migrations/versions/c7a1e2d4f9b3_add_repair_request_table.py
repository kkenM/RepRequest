"""add repair_request table

Revision ID: c7a1e2d4f9b3
Revises: 59d5d89e610f
Create Date: 2026-11-03 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7a1e2d4f9b3'
down_revision = '59d5d89e610f'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('repair_request',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('company_id', sa.Integer(), nullable=False),
    sa.Column('machine_id', sa.Integer(), nullable=False),
    sa.Column('reported_by_id', sa.Integer(), nullable=True),
    sa.Column('severity', sa.String(length=10), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(), nullable=False),
    sa.ForeignKeyConstraint(['company_id'], ['company.id'], ),
    sa.ForeignKeyConstraint(['machine_id'], ['machine.id'], ),
    sa.ForeignKeyConstraint(['reported_by_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_repair_request_machine_id'), ['machine_id'], unique=False)
        batch_op.create_index('ix_repair_request_queue', ['company_id', 'status', 'severity'], unique=False)


def downgrade():
    with op.batch_alter_table('repair_request', schema=None) as batch_op:
        batch_op.drop_index('ix_repair_request_queue')
        batch_op.drop_index(batch_op.f('ix_repair_request_machine_id'))

    op.drop_table('repair_request')
