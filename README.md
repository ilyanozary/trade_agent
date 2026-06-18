# TradePilot AI Backend

مستندات کامل فارسی پروژه: [docs/TRADEPILOT_DOCUMENTATION_FA.md](docs/TRADEPILOT_DOCUMENTATION_FA.md)

Development-first Flask and Next.js application for testing TradePilot AI paper trading. It does not implement real trading or connect to exchange order endpoints.

## Stack

- Python 3.11+
- Flask
- Flask SQLAlchemy
- Flask JWT Extended
- Flask Migrate
- PostgreSQL
- Flask CORS
- Marshmallow validation
- Virtual paper trading with EMA/RSI/ATR signals and optional GPT risk filtering

## Setup

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Set the values in `.env`, including `DATABASE_URL`, `SECRET_KEY`, and `JWT_SECRET_KEY`.

## Docker

Create a local environment file:

```bash
cp .env.example .env
```

Generate secure values for `SECRET_KEY` and `JWT_SECRET_KEY`:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Then start the full stack:

```bash
docker compose up --build
```

For a completely empty development database, remove the previous PostgreSQL volume first:

```bash
docker compose down -v
docker compose up --build
```

Services:

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5000`
- PostgreSQL: `localhost:5432`

The backend container waits for PostgreSQL, runs `flask db upgrade`, then starts the Flask debug server.

The current Compose setup runs in development mode with hot reload for Flask and Next.js. The first screen is registration. Use:

```text
Username: ilyanozary
Password: ilyalm10
```

Registration automatically creates a long-lived development subscription, an enabled paper-only bot profile, and a virtual account with 10,000 USDT. No email service or exchange API is required.

Useful commands:

```bash
docker compose logs -f backend
docker compose exec backend flask --app run.py db current
docker compose exec postgres psql -U tradepilot -d tradepilot_ai
docker compose down
docker compose down -v
```

## Database

If you are running without Docker, create the PostgreSQL database, then run migrations:

```bash
flask --app run.py db upgrade
```

The initial migration is already included in `migrations/versions`.

Start the API:

```bash
flask --app run.py run --host 0.0.0.0 --port 5000
```

For production, run with Gunicorn:

```bash
gunicorn "run:app"
```

## Environment Variables

- `FLASK_ENV`: Flask environment, usually `development` locally.
- `SECRET_KEY`: Flask secret key.
- `JWT_SECRET_KEY`: JWT signing secret.
- `DATABASE_URL`: PostgreSQL SQLAlchemy URL.
- `CORS_ORIGINS`: Comma-separated frontend origins.
- `USDT_TRC20_WALLET_ADDRESS`: Destination wallet for USDT TRC20 invoices.
- `MARKET_DATA_PROVIDER`: `mock` for offline simulation or `bitunix` for real public Bitunix Futures data. API failures never fall back to mock data.
- `ENCRYPTION_KEY`: Fernet key used to encrypt exchange credentials at rest.
- `LIVE_TRADING_API_ENABLED`: Server-side live-order gate. Keep `false` until the deployment and risk controls have been reviewed.
- `OPENAI_API_KEY`: Optional key for the GPT confidence layer.
- `OPENAI_MODEL`: GPT validation model, default `gpt-4o-mini`.
- `PAPER_TRADING_INITIAL_BALANCE`: Initial virtual USDT balance, default `10000`.
- `PAPER_TRADING_DEFAULT_LEVERAGE`: Default simulation leverage, default `1`.
- `PAPER_CONFIDENCE_THRESHOLD`: Fallback minimum confidence, default `70`.

## API Endpoints

Auth:

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/auth/logout`

Subscriptions:

- `GET /api/subscriptions/plans`
- `GET /api/subscriptions/current`

Payments:

- `POST /api/payments/create`
- `GET /api/payments/<payment_id>`
- `POST /api/payments/<payment_id>/submit-tx`

Admin payments:

- `GET /api/admin/payments`
- `POST /api/admin/payments/<payment_id>/confirm`
- `POST /api/admin/payments/<payment_id>/reject`

Bot profile:

- `GET /api/bot/profile`
- `POST /api/bot/profile`
- `PATCH /api/bot/profile`

Dashboard:

- `GET /api/dashboard/overview`

Paper trading:

- `GET /api/paper/account`
- `POST /api/paper/account/reset`
- `GET /api/paper/positions`
- `POST /api/paper/positions/open`
- `POST /api/paper/positions/<position_id>/close`
- `GET /api/paper/trades`
- `GET /api/paper/signals`
- `POST /api/paper/engine/run-once`

## Paper Trading V1

Paper Trading V1 simulates positions using virtual USDT only. Supported mock markets are BTCUSDT, ETHUSDT, SOLUSDT, DOGEUSDT, AVAXUSDT, and LINKUSDT. The smaller markets intentionally use wider simulation volatility profiles for testing. Its execution flow is:

1. Generate mock BTCUSDT or ETHUSDT OHLCV candles.
2. Calculate EMA50, EMA200, RSI14, ATR14, and volume alignment.
3. Generate a rule-based `LONG`, `SHORT`, or `HOLD` signal.
4. Optionally send the pre-generated signal to GPT as a conservative risk filter.
5. Apply subscription, bot mode, confidence, duplicate-position, balance, and sizing checks.
6. Open a virtual position and monitor its stop loss and take profit.
7. Record virtual PnL, closed trades, and signal history.

GPT cannot invent an opposite direction or bypass risk controls. It may only confirm the strategy action or downgrade it to `HOLD`. GPT confidence is capped at the rule-based strategy confidence. If `OPENAI_API_KEY` is empty, the system uses rule-based confidence.

Apply database migrations after updating:

```bash
flask --app run.py db upgrade
```

Configure the bot in `paper` mode and enable it, then trigger one cycle:

```bash
curl -X POST http://localhost:5000/api/paper/engine/run-once \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

Open a manual virtual position for testing:

```bash
curl -X POST http://localhost:5000/api/paper/positions/open \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "LONG",
    "entry_price": 100000,
    "stop_loss": 99000,
    "take_profit": 102000,
    "margin_usdt": 100,
    "leverage": 1,
    "confidence": 75
  }'
```

Close at the latest mock market price:

```bash
curl -X POST http://localhost:5000/api/paper/positions/1/close \
  -H "Authorization: Bearer $ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

The optional CLI command is:

```bash
flask --app run.py paper-engine run-once --user-id 1
```

Important: this module is simulated trading only. It does not send exchange orders, does not guarantee results, and must not be treated as evidence of future profitability.

## Payment Flow

1. User registers or logs in and receives a JWT access token.
2. Frontend calls `GET /api/subscriptions/plans` to display Starter and Pro plans.
3. User selects a plan and calls `POST /api/payments/create`.
4. Backend creates a pending USDT TRC20 invoice using `USDT_TRC20_WALLET_ADDRESS`.
5. User sends USDT externally and submits the transaction hash via `POST /api/payments/<payment_id>/submit-tx`.
6. Payment status becomes `submitted`.
7. Admin reviews the transaction manually.
8. Admin calls `POST /api/admin/payments/<payment_id>/confirm`.
9. Backend marks payment as `confirmed` and creates or extends the user subscription.

The backend never auto-confirms payments and does not perform exchange trading.

## Security Notes

- Passwords are hashed with Werkzeug.
- JWT access tokens are required for protected endpoints.
- Logout stores token JTIs in a persistent blocklist table.
- Admin endpoints require `role=admin`.
- CORS origins are read from environment configuration.
