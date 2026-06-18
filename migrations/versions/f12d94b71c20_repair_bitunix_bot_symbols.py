"""repair profiles unsupported by Bitunix provider

Revision ID: f12d94b71c20
Revises: e9a4c2f8d101
"""
from alembic import op
import sqlalchemy as sa

revision = "f12d94b71c20"
down_revision = "e9a4c2f8d101"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(sa.text("UPDATE bot_profiles SET symbol = 'BTCUSDT' WHERE symbol NOT IN ('BTCUSDT', 'ETHUSDT', 'SOLUSDT')"))


def downgrade():
    pass
