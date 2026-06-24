#!/bin/sh
set -e

if [ ! -x node_modules/.bin/next ]; then
  echo "Frontend dependencies are missing in mounted node_modules; running npm ci..."
  npm ci --legacy-peer-deps
fi

exec "$@"
