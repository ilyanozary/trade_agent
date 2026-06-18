import json
import time

import click
from flask import Flask

from app.extensions import db
from app.services.paper_trading_engine import run_paper_engine_for_user
from app.services.paper_trading_engine import tick_paper_engine_for_user
from app.models import BotProfile
from app.services.market_data_service import get_supported_symbols


def register_cli(app: Flask) -> None:
    @app.cli.group("paper-engine")
    def paper_engine():
        """Run paper trading simulation commands."""

    @paper_engine.command("run-once")
    @click.option("--user-id", required=True, type=int)
    def run_once(user_id: int):
        """Run one simulation cycle for a user."""
        result = run_paper_engine_for_user(user_id)
        click.echo(json.dumps(result, indent=2))

    @paper_engine.command("run-worker")
    @click.option("--tick-seconds", default=2, type=int, show_default=True)
    @click.option("--analysis-seconds", default=30, type=int, show_default=True)
    def run_worker(tick_seconds: int, analysis_seconds: int):
        """Continuously monitor enabled paper bots and periodically analyze signals."""
        click.echo("[paper-worker] started; simulation only, no exchange orders")
        last_analysis: dict[int, float] = {}
        while True:
            profiles = BotProfile.query.filter_by(mode="paper", is_enabled=True).all()
            now = time.monotonic()
            for profile in profiles:
                try:
                    if profile.symbol not in get_supported_symbols():
                        previous_symbol = profile.symbol
                        profile.symbol = "BTCUSDT"
                        db.session.commit()
                        click.echo(
                            f"[paper-worker] repaired user={profile.user_id} "
                            f"unsupported_symbol={previous_symbol} fallback=BTCUSDT",
                        )
                    tick = tick_paper_engine_for_user(profile.user_id)
                    click.echo(
                        f"[paper-worker] tick user={profile.user_id} symbol={profile.symbol} "
                        f"price={tick['latest_price']:.4f} positions={len(tick['open_positions'])} "
                        f"equity={tick['account']['equity_usdt']:.2f}",
                    )
                    if now - last_analysis.get(profile.user_id, 0) >= analysis_seconds:
                        result = run_paper_engine_for_user(profile.user_id)
                        click.echo(
                            f"[paper-worker] analysis user={profile.user_id} "
                            f"strategy={result['strategy_signal']['action']} "
                            f"base={result['strategy_signal']['confidence_base']} "
                            f"gpt={result['ai_signal']['action']}:{result['ai_signal']['confidence']} "
                            f"what_if_long={result['scenario_comparison']['long']['confidence']} "
                            f"what_if_short={result['scenario_comparison']['short']['confidence']} "
                            f"opened={result['position_opened']} reason={result['reason']}",
                        )
                        last_analysis[profile.user_id] = now
                except Exception as exc:
                    db.session.rollback()
                    click.echo(f"[paper-worker] error user={profile.user_id}: {exc}", err=True)
            time.sleep(max(1, tick_seconds))
