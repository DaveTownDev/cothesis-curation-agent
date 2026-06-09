#!/usr/bin/env bash
# Console E2E smoke: auth gate, protected routes, Firestore-backed pages.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONSOLE="$ROOT/console"
PORT="${E2E_PORT:-3099}"
BASE="http://127.0.0.1:$PORT"
COOKIE_JAR="$(mktemp)"
LOG="$(mktemp)"
PID=""

cleanup() {
  if [[ -n "$PID" ]] && kill -0 "$PID" 2>/dev/null; then
    kill "$PID" 2>/dev/null || true
    wait "$PID" 2>/dev/null || true
  fi
  rm -f "$COOKIE_JAR" "$LOG"
}
trap cleanup EXIT

if [[ ! -f "$CONSOLE/.env.local" ]]; then
  echo "FAIL: $CONSOLE/.env.local missing (copy from main repo .env / console/.env.local)"
  exit 1
fi

# shellcheck disable=SC1091
set -a && source "$CONSOLE/.env.local" && set +a
if [[ -z "${CONSOLE_LOGIN_SECRET:-}" ]]; then
  echo "FAIL: CONSOLE_LOGIN_SECRET not set in .env.local"
  exit 1
fi

cd "$CONSOLE"
npm run dev -- --port "$PORT" >"$LOG" 2>&1 &
PID=$!

for _ in $(seq 1 60); do
  if curl -sf "$BASE/login" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
if ! curl -sf "$BASE/login" >/dev/null 2>&1; then
  echo "FAIL: dev server did not start"
  tail -30 "$LOG"
  exit 1
fi

pass() { echo "  OK: $1"; }
fail() { echo "FAIL: $1"; exit 1; }

curl -sf "$BASE/login" | grep -qi "passcode" || fail "login page missing passcode field"
pass "GET /login"

code=$(curl -s -o /dev/null -w "%{http_code}" "$BASE/dashboard")
[[ "$code" == "307" || "$code" == "302" ]] || fail "unauthenticated /dashboard expected redirect, got $code"
pass "GET /dashboard unauthenticated redirects"

wrong_headers=$(curl -si -X POST "$BASE/api/auth/login" -F "passcode=wrong-passcode-smoke-test")
echo "$wrong_headers" | grep -qi "login?error=1" || fail "wrong passcode expected redirect to login?error=1"
pass "POST /api/auth/login wrong passcode redirects"

login_headers=$(curl -si -c "$COOKIE_JAR" -X POST "$BASE/api/auth/login" -F "passcode=$CONSOLE_LOGIN_SECRET")
echo "$login_headers" | grep -qi "cothesis_session" || fail "login missing session cookie"
echo "$login_headers" | grep -qi "dashboard" || fail "login missing dashboard redirect"
pass "POST /api/auth/login success"

page_has() { grep -qi "$1" <<< "$2"; }

for path in dashboard review resources pipeline; do
  body=$(curl -sf -b "$COOKIE_JAR" "$BASE/$path")
  page_has "cothesis\|review\|published\|pipeline\|dashboard" "$body" || fail "$path returned unexpected body"
  pass "GET /$path authenticated"
done

review_html=$(curl -sf -b "$COOKIE_JAR" "$BASE/review")
if grep -q 'href="/review/' <<< "$review_html"; then
  item_path=$(grep -o 'href="/review/[^"]*"' <<< "$review_html" | head -1 | cut -d'"' -f2)
  detail=$(curl -sf -b "$COOKIE_JAR" "$BASE$item_path")
  page_has "approve\|decision\|description" "$detail" || fail "review detail missing expected UI"
  pass "GET $item_path review detail"
else
  echo "  SKIP: no pending review items in queue"
fi

echo ""
echo "E2E smoke passed ($BASE)"
