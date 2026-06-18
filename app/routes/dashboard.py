from flask import Blueprint

from app.extensions import db
from app.models import BotProfile, PaperPosition, PaperSignal, PaperTrade
from app.services.paper_trading_engine import get_or_create_paper_account, refresh_account_totals
from app.services.subscription_service import get_current_subscription
from app.utils.decorators import current_user, subscription_required
from app.utils.responses import success_response

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.get("/overview")
@subscription_required
def overview():
    user = current_user()
    subscription = get_current_subscription(user.id)
    bot_profile = BotProfile.query.filter_by(user_id=user.id).first()
    paper_account = get_or_create_paper_account(user.id)
    refresh_account_totals(paper_account)
    recent_paper_trades = (
        PaperTrade.query.filter_by(user_id=user.id).order_by(PaperTrade.closed_at.desc()).limit(10).all()
    )
    latest_paper_signals = (
        PaperSignal.query.filter_by(user_id=user.id).order_by(PaperSignal.created_at.desc()).limit(10).all()
    )
    open_positions_count = PaperPosition.query.filter_by(user_id=user.id, status="open").count()
    db.session.commit()

    data = {
        "account_balance": 0,
        "daily_pnl": 0,
        "open_positions_count": open_positions_count,
        "bot_status": "enabled" if bot_profile and bot_profile.is_enabled else "disabled",
        "subscription_status": subscription.status if subscription else "inactive",
        "current_plan": subscription.plan_name if subscription else None,
        "subscription_expires_at": subscription.expires_at.isoformat() if subscription else None,
        "recent_trades": [],
        "paper_balance": float(paper_account.balance_usdt),
        "paper_equity": float(paper_account.equity_usdt),
        "paper_realized_pnl": float(paper_account.realized_pnl),
        "paper_unrealized_pnl": float(paper_account.unrealized_pnl),
        "recent_paper_trades": [trade.to_dict() for trade in recent_paper_trades],
        "latest_paper_signals": [signal.to_dict() for signal in latest_paper_signals],
    }
    return success_response(data)
