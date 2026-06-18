"""add bitunix connection and live trading

Revision ID: e9a4c2f8d101
Revises: d7e2a9104c31
"""
from alembic import op
import sqlalchemy as sa

revision = "e9a4c2f8d101"
down_revision = "d7e2a9104c31"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("bot_profiles") as batch:
        batch.add_column(sa.Column("live_trading_enabled", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch.add_column(sa.Column("risk_disclaimer_accepted_at", sa.DateTime(timezone=True), nullable=True))
        batch.add_column(sa.Column("max_leverage", sa.Integer(), nullable=False, server_default="2"))
        batch.add_column(sa.Column("max_open_positions", sa.Integer(), nullable=False, server_default="1"))
    op.create_table("exchange_api_keys", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("exchange", sa.String(40), nullable=False), sa.Column("api_key_encrypted", sa.Text(), nullable=False), sa.Column("api_secret_encrypted", sa.Text(), nullable=False), sa.Column("is_connected", sa.Boolean(), nullable=False), sa.Column("last_validated_at", sa.DateTime(timezone=True)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id", "exchange", name="uq_user_exchange_key"))
    op.create_index("ix_exchange_api_keys_user_id", "exchange_api_keys", ["user_id"])
    op.create_table("live_risk_states", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("trading_date", sa.Date(), nullable=False), sa.Column("daily_realized_pnl", sa.Numeric(18,8), nullable=False), sa.Column("starting_balance", sa.Numeric(18,8)), sa.Column("kill_switch_active", sa.Boolean(), nullable=False), sa.Column("last_reason", sa.String(255)), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False), sa.UniqueConstraint("user_id"))
    op.create_table("live_positions", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("exchange_position_id", sa.String(100)), sa.Column("exchange_order_id", sa.String(100), nullable=False), sa.Column("symbol", sa.String(30), nullable=False), sa.Column("side", sa.String(10), nullable=False), sa.Column("quantity", sa.Numeric(24,10), nullable=False), sa.Column("entry_price", sa.Numeric(24,10)), sa.Column("stop_loss", sa.Numeric(24,10), nullable=False), sa.Column("take_profit", sa.Numeric(24,10), nullable=False), sa.Column("leverage", sa.Integer(), nullable=False), sa.Column("confidence", sa.Integer(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("live_trades", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("symbol", sa.String(30), nullable=False), sa.Column("side", sa.String(10), nullable=False), sa.Column("exchange_order_id", sa.String(100), nullable=False), sa.Column("entry_price", sa.Numeric(24,10)), sa.Column("exit_price", sa.Numeric(24,10)), sa.Column("quantity", sa.Numeric(24,10), nullable=False), sa.Column("pnl_usdt", sa.Numeric(18,8)), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_table("live_order_logs", sa.Column("id", sa.Integer(), primary_key=True), sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False), sa.Column("endpoint", sa.String(255), nullable=False), sa.Column("request_payload", sa.Text(), nullable=False), sa.Column("response_payload", sa.Text(), nullable=False), sa.Column("status", sa.String(30), nullable=False), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))


def downgrade():
    for table in ("live_order_logs", "live_trades", "live_positions", "live_risk_states", "exchange_api_keys"):
        op.drop_table(table)
    with op.batch_alter_table("bot_profiles") as batch:
        for column in ("max_open_positions", "max_leverage", "risk_disclaimer_accepted_at", "live_trading_enabled"):
            batch.drop_column(column)
