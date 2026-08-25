#!/usr/bin/env bash
# Idempotent repository setup for The Dispatch Markets Cloud Agent environment.
# - installs Node dependencies (rewriting the committed lockfile's Replit-internal
#   package host to the public npm registry so `npm ci` works outside Replit)
# - initializes a local PostgreSQL cluster + application database (the app talks to
#   Postgres via the Neon serverless HTTP driver, backed locally by neon-http-proxy.js)
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PG_BIN="/usr/lib/postgresql/16/bin"
export PATH="$PG_BIN:$PATH"
PGDATA="${DISPATCH_PGDATA:-$HOME/dispatch-pgdata}"
PGPORT="${DISPATCH_PGPORT:-5432}"

echo "==> Ensuring PostgreSQL is installed"
if [ ! -x "$PG_BIN/initdb" ]; then
  echo "    installing postgresql via apt"
  sudo apt-get update -qq
  sudo apt-get install -y -qq postgresql postgresql-contrib
else
  echo "    PostgreSQL already installed"
fi

echo "==> Installing Node dependencies"
# The committed package-lock.json pins tarball hosts at package-firewall.replit.local,
# which only resolves inside Replit. Point resolved URLs at the public registry.
if grep -q 'package-firewall\.replit\.local' package-lock.json; then
  sed -i 's#http://package-firewall\.replit\.local/npm/#https://registry.npmjs.org/#g' package-lock.json
  echo "    rewrote Replit package host -> registry.npmjs.org in package-lock.json"
fi
npm ci --no-audit --no-fund

echo "==> Ensuring local PostgreSQL cluster at $PGDATA"
if [ ! -f "$PGDATA/PG_VERSION" ]; then
  mkdir -p "$PGDATA"
  initdb -D "$PGDATA" -U postgres --auth=trust -E UTF8 >/tmp/dispatch-initdb.log 2>&1
  echo "    initialized new cluster"
else
  echo "    cluster already present"
fi

# Temporarily start the cluster to ensure the role + database exist, then leave it
# running (start.sh reconciles it on every boot regardless).
if ! pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
  pg_ctl -D "$PGDATA" \
    -o "-c listen_addresses='127.0.0.1' -p $PGPORT -c unix_socket_directories='/tmp'" \
    -l /tmp/dispatch-pg.log -w start
fi

psql -h 127.0.0.1 -U postgres -p "$PGPORT" -tc "SELECT 1 FROM pg_roles WHERE rolname='dispatch'" | grep -q 1 \
  || psql -h 127.0.0.1 -U postgres -p "$PGPORT" -c "CREATE ROLE dispatch LOGIN PASSWORD 'dispatch' SUPERUSER"
psql -h 127.0.0.1 -U postgres -p "$PGPORT" -tc "SELECT 1 FROM pg_database WHERE datname='dispatch'" | grep -q 1 \
  || psql -h 127.0.0.1 -U postgres -p "$PGPORT" -c "CREATE DATABASE dispatch OWNER dispatch"

echo "==> Install complete"
