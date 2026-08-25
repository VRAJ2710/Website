#!/usr/bin/env bash
# Runs The Dispatch Markets preview server in the foreground (used as the
# environment's `app` terminal). Routes the Neon serverless HTTP driver at the
# local proxy so the unmodified app runs against local PostgreSQL.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$REPO_ROOT"

PGPORT="${DISPATCH_PGPORT:-5432}"
PROXY_PORT="${NEON_LOCAL_PROXY_PORT:-5433}"

export PORT="${PORT:-5000}"
export DATABASE_URL="${DATABASE_URL:-postgresql://dispatch:dispatch@127.0.0.1:${PGPORT}/dispatch}"
export NEON_LOCAL_PROXY_URL="${NEON_LOCAL_PROXY_URL:-http://127.0.0.1:${PROXY_PORT}/sql}"

exec node --require "$REPO_ROOT/.cursor/dev/neon-fetch-shim.js" server.js
