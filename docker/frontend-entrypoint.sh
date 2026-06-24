#!/bin/sh
set -e

if [ ! -x /opt/frontend_deps/node_modules/.bin/next ]; then
  echo "Frontend dependency cache is missing from the image. Rebuild frontend with --no-cache." >&2
  exit 1
fi

rm -rf node_modules
ln -s /opt/frontend_deps/node_modules node_modules

export PATH="/opt/frontend_deps/node_modules/.bin:$PATH"
exec "$@"
