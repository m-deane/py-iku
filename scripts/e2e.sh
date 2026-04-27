#!/usr/bin/env bash
# e2e.sh — local / CI launcher for Playwright e2e tests.
#
# Starts the FastAPI dev server and the Vite dev server in the background,
# waits for both to be healthy, runs Playwright, then cleans up.
#
# Usage (from repo root):
#   bash scripts/e2e.sh [extra playwright args]
#
# Examples:
#   bash scripts/e2e.sh --project=chromium
#   bash scripts/e2e.sh --headed
#   bash scripts/e2e.sh tests/e2e/smoke.spec.ts
#
# Environment variables (all optional):
#   API_PORT   default 8000
#   WEB_PORT   default 5173
#   API_WAIT   seconds to wait for API  (default 60)
#   WEB_WAIT   seconds to wait for web  (default 60)

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
API_PORT="${API_PORT:-8000}"
WEB_PORT="${WEB_PORT:-5173}"
API_WAIT="${API_WAIT:-60}"
WEB_WAIT="${WEB_WAIT:-60}"

API_PID=""
WEB_PID=""

cleanup() {
  echo ""
  echo "==> Cleaning up background processes..."
  [[ -n "$API_PID" ]] && kill "$API_PID" 2>/dev/null || true
  [[ -n "$WEB_PID" ]] && kill "$WEB_PID" 2>/dev/null || true
  wait 2>/dev/null || true
  echo "==> Done."
}
trap cleanup EXIT

# ── Start API ─────────────────────────────────────────────────────────────────
echo "==> Starting FastAPI on port $API_PORT..."
(
  cd "$REPO_ROOT/apps/api"
  # Ensure py2dataiku is importable from the monorepo root.
  export PYTHONPATH="$REPO_ROOT:${PYTHONPATH:-}"
  uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT" 2>&1
) &
API_PID=$!

# ── Start web dev server ───────────────────────────────────────────────────────
echo "==> Starting Vite dev server on port $WEB_PORT..."
(
  cd "$REPO_ROOT/apps/web"
  pnpm dev --host 127.0.0.1 --port "$WEB_PORT" 2>&1
) &
WEB_PID=$!

# ── Wait for both services ────────────────────────────────────────────────────
echo "==> Waiting for API health check..."
(
  cd "$REPO_ROOT/apps/web"
  pnpm exec tsx scripts/wait-for-port.ts "http://127.0.0.1:$API_PORT/health" "$API_WAIT"
)

echo "==> Waiting for web dev server..."
(
  cd "$REPO_ROOT/apps/web"
  pnpm exec tsx scripts/wait-for-port.ts "http://127.0.0.1:$WEB_PORT" "$WEB_WAIT"
)

# ── Run Playwright ────────────────────────────────────────────────────────────
echo "==> Running Playwright..."
export BASE_URL="http://127.0.0.1:$WEB_PORT"
export API_URL="http://127.0.0.1:$API_PORT"
export CI="${CI:-}"

cd "$REPO_ROOT/apps/web"
pnpm exec playwright test "$@"
