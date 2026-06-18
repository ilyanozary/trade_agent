"""add username authentication

Revision ID: 1ea50a500b9c
Revises: b005620d49fe
Create Date: 2026-06-12 15:42:09.147305

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1ea50a500b9c'
down_revision = 'b005620d49fe'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('username', sa.String(length=80), nullable=True))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=255),
               nullable=True)

    connection = op.get_bind()
    user_ids = connection.execute(sa.text("SELECT id FROM users")).scalars().all()
    for user_id in user_ids:
        connection.execute(
            sa.text("UPDATE users SET username = :username WHERE id = :user_id"),
            {"username": f"legacy_user_{user_id}", "user_id": user_id},
        )

    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.alter_column('username', existing_type=sa.String(length=80), nullable=False)
        batch_op.create_index(batch_op.f('ix_users_username'), ['username'], unique=True)


def downgrade():
    connection = op.get_bind()
    connection.execute(
        sa.text(
            "UPDATE users SET email = username || '@local.invalid' "
            "WHERE email IS NULL"
        )
    )
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_users_username'))
        batch_op.alter_column('email',
               existing_type=sa.VARCHAR(length=255),
               nullable=False)
        batch_op.drop_column('username')
