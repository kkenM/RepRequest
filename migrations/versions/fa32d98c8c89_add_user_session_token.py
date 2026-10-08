"""add user session token

Revision ID: fa32d98c8c89
Revises: e20531516603
Create Date: 2026-10-07 15:54:24.805389

"""
import secrets
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fa32d98c8c89'
down_revision = 'e20531516603'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Add the column, allowing nulls for existing rows.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.add_column(
            sa.Column('session_token', sa.String(length=64), nullable=True)
        )

    # 2. Give every existing user a token.
    connection = op.get_bind()
    user_table = sa.table(
        'user',
        sa.column('id', sa.Integer),
        sa.column('session_token', sa.String)
    )

    for (user_id,) in connection.execute(sa.select(user_table.c.id)):
        connection.execute(
            user_table.update()
            .where(user_table.c.id == user_id)
            .values(session_token=secrets.token_urlsafe(32))
        )

    # 3. Make it required and unique.
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.alter_column(
            'session_token',
            existing_type=sa.String(length=64),
            nullable=False
        )
        batch_op.create_unique_constraint(
            'uq_user_session_token',
            ['session_token']
        )


def downgrade():
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_constraint('uq_user_session_token', type_='unique')
        batch_op.drop_column('session_token')

    # ### end Alembic commands ###
