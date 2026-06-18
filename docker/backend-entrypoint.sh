#!/bin/sh
set -e

python <<'PY'
import time
from sqlalchemy import create_engine, text
from app.config import Config

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI, pool_pre_ping=True)
last_error = None

for attempt in range(1, 31):
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        print("Database is ready")
        break
    except Exception as exc:
        last_error = exc
        print(f"Waiting for database... attempt {attempt}/30")
        time.sleep(2)
else:
    raise SystemExit(f"Database did not become ready: {last_error}")
PY

if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
  flask --app run.py db upgrade
fi

exec "$@"
