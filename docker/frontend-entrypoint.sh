#!/bin/sh
set -e

if [ ! -x node_modules/.bin/next ]; then
  echo "Frontend dependencies are missing in mounted node_modules; restoring from image cache..."
  rm -rf node_modules
  cp -a /opt/frontend_node_modules node_modules
fi

exec "$@"
