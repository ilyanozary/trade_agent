from flask import current_app


def get_usdt_trc20_wallet_address() -> str:
    wallet_address = current_app.config["USDT_TRC20_WALLET_ADDRESS"]
    if not wallet_address:
        raise RuntimeError("USDT_TRC20_WALLET_ADDRESS is not configured")
    return wallet_address
