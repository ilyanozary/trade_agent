#!/bin/sh
set -e

if [ ! -x node_modules/.bin/next ]; then
  echo "Frontend dependencies are missing in mounted node_modules; restoring from image cache..."
  mkdir -p node_modules
  find node_modules -mindepth 1 -maxdepth 1 -exec rm -rf {} +
  cp -a /opt/frontend_node_modules/. node_modules/
fi

exec "$@"
