#!/bin/sh
set -e

if [ ! -x /opt/frontend_node_modules/.bin/next ]; then
  echo "Frontend dependency cache is missing; rebuilding it..."
  npm ci --legacy-peer-deps
  rm -rf /opt/frontend_node_modules
  cp -a node_modules /opt/frontend_node_modules
fi

rm -rf node_modules
ln -s /opt/frontend_node_modules node_modules

export PATH="/opt/frontend_node_modules/.bin:$PATH"
exec "$@"
