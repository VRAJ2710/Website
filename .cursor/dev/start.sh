#!/usr/bin/env bash
# Per-boot service reconciliation for The Dispatch Markets. Brings up the local
# PostgreSQL cluster and the Neon HTTP -> Postgres proxy, waits until both are
# ready, then returns. The application itself runs as a foreground terminal.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PG_BIN="/usr/lib/postgresql/16/bin"
export PATH="$PG_BIN:$PATH"
PGDATA="${DISPATCH_PGDATA:-$HOME/dispatch-pgdata}"
PGPORT="${DISPATCH_PGPORT:-5432}"
PROXY_PORT="${NEON_LOCAL_PROXY_PORT:-5433}"

echo "==> Starting PostgreSQL (data dir: $PGDATA, port: $PGPORT)"
if pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
  echo "    already running"
else
  pg_ctl -D "$PGDATA" \
    -o "-c listen_addresses='127.0.0.1' -p $PGPORT -c unix_socket_directories='/tmp'" \
    -l /tmp/dispatch-pg.log -w start
fi

# Wait for Postgres to accept connections.
for _ in $(seq 1 30); do
  if pg_isready -h 127.0.0.1 -p "$PGPORT" -q; then break; fi
  sleep 0.5
done
pg_isready -h 127.0.0.1 -p "$PGPORT" -q && echo "    PostgreSQL ready"

echo "==> Starting Neon HTTP proxy on port $PROXY_PORT"
if curl -sf "http://127.0.0.1:${PROXY_PORT}/health" >/dev/null 2>&1; then
  echo "    already running"
else
  nohup env NEON_LOCAL_PROXY_PORT="$PROXY_PORT" \
    node "$REPO_ROOT/.cursor/dev/neon-http-proxy.js" >/tmp/dispatch-neon-proxy.log 2>&1 &
  for _ in $(seq 1 30); do
    if curl -sf "http://127.0.0.1:${PROXY_PORT}/health" >/dev/null 2>&1; then break; fi
    sleep 0.5
  done
  curl -sf "http://127.0.0.1:${PROXY_PORT}/health" >/dev/null 2>&1 && echo "    Neon proxy ready"
fi

echo "==> Services ready"
