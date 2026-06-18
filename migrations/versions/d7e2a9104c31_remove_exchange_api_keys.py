"""remove exchange api keys

Revision ID: d7e2a9104c31
Revises: 1ea50a500b9c
"""

from alembic import op
import sqlalchemy as sa


revision = "d7e2a9104c31"
down_revision = "1ea50a500b9c"
branch_labels = None
depends_on = None


def upgrade():
    op.drop_table("exchange_api_keys")


def downgrade():
    op.create_table(
        "exchange_api_keys",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("exchange", sa.String(length=40), nullable=False),
        sa.Column("api_key_encrypted", sa.Text(), nullable=False),
        sa.Column("api_secret_encrypted", sa.Text(), nullable=False),
        sa.Column("is_connected", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "exchange", name="uq_user_exchange_key"),
    )
    op.create_index("ix_exchange_api_keys_user_id", "exchange_api_keys", ["user_id"])
