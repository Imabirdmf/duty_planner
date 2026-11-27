#!/usr/bin/env bash
# Driver for running DutyPlanner locally (Django API + Vite frontend) against a
# throwaway SQLite DB. Run from the repo root.
#
#   driver.sh up          # fresh DB, migrate, seed, start backend :8000 + frontend :5173
#   driver.sh login       # log in as the seeded admin, store JWT cookies
#   driver.sh api METHOD PATH [JSON]   # call the API with the stored cookies
#   driver.sh screenshot [URL] [OUT]   # headless Chrome screenshot (default: frontend)
#   driver.sh smoke       # end-to-end check: list, retrieve, generate, screenshot
#   driver.sh down        # stop both servers
#
# State lives in $RUN_DIR (default: <repo>/.run-local, gitignored): dev.sqlite3, logs,
# cookies, screenshots.
set -euo pipefail

ROOT="$(git rev-parse --show-toplevel)"
RUN_DIR="${RUN_DIR:-$ROOT/.run-local}"
API="http://localhost:8000/api"
FRONT="http://localhost:5173"
CHROME="${CHROME:-/Applications/Google Chrome.app/Contents/MacOS/Google Chrome}"
ADMIN_EMAIL="admin@example.com"
ADMIN_PASS="admin-pass-123"
mkdir -p "$RUN_DIR"

# Env vars take precedence over backend/.env (load_dotenv doesn't override),
# so this never touches the Postgres configured there. Placeholders = CI values.
export DATABASE_URL="sqlite:///$RUN_DIR/dev.sqlite3"
export SECRET_KEY="${SECRET_KEY:-local-dev-secret}"
export FRONTEND_URL="${FRONTEND_URL:-$FRONT}"
export JIRA_BASE_URL="${JIRA_BASE_URL:-https://placeholder.atlassian.net}"
export JIRA_EMAIL="${JIRA_EMAIL:-placeholder@example.com}"
export JIRA_API_TOKEN="${JIRA_API_TOKEN:-placeholder}"
export JIRA_PROJECT_KEY="${JIRA_PROJECT_KEY:-PLACEHOLDER}"
export JIRA_PARENT_ISSUE_KEY="${JIRA_PARENT_ISSUE_KEY:-PLACEHOLDER-1}"

manage() { (cd "$ROOT" && uv run backend/manage.py "$@"); }

wait_for() {
  for _ in $(seq 1 40); do curl -s -o /dev/null "$1" && return 0; sleep 0.5; done
  echo "timeout waiting for $1" >&2; return 1
}

cmd_up() {
  cmd_down >/dev/null 2>&1 || true
  rm -f "$RUN_DIR/dev.sqlite3" "$RUN_DIR/cookies.txt"
  (cd "$ROOT" && uv sync --python 3.13 -q)
  manage migrate -v0
  manage shell -v0 -c "
from django.contrib.auth import get_user_model
from planner.models import Staff
get_user_model().objects.create_superuser(email='$ADMIN_EMAIL', password='$ADMIN_PASS')
for i, (f, l, active) in enumerate([
    ('Анна', 'Активная', True), ('Борис', 'Активный', True),
    ('Вера', 'Активная', True), ('Глеб', 'Неактивный', False)]):
    Staff.objects.create(first_name=f, last_name=l, email=f'u{i}@example.com', is_active=active)
"
  (cd "$ROOT" && nohup uv run backend/manage.py runserver 8000 >"$RUN_DIR/backend.log" 2>&1 </dev/null &)
  [ -d "$ROOT/frontend/node_modules" ] || (cd "$ROOT/frontend" && npm ci)
  (cd "$ROOT/frontend" && nohup npm run dev -- --port 5173 --strictPort >"$RUN_DIR/frontend.log" 2>&1 </dev/null &)
  wait_for "$API/users/"; wait_for "$FRONT"
  echo "backend $API  frontend $FRONT  admin $ADMIN_EMAIL / $ADMIN_PASS  logs $RUN_DIR"
}

cmd_login() {
  curl -sf -c "$RUN_DIR/cookies.txt" -H 'Content-Type: application/json' \
    -d "{\"email\":\"$ADMIN_EMAIL\",\"password\":\"$ADMIN_PASS\"}" "$API/auth/login/" >/dev/null
  echo "logged in"
}

cmd_api() {
  local method="$1" path="$2" body="${3:-}"
  curl -s -b "$RUN_DIR/cookies.txt" -X "$method" -H 'Content-Type: application/json' \
    ${body:+-d "$body"} "$API$path"; echo
}

cmd_screenshot() {
  local url="${1:-$FRONT}" out="${2:-$RUN_DIR/front.png}"
  "$CHROME" --headless=new --disable-gpu --user-data-dir="$RUN_DIR/chrome" \
    --window-size=1400,1000 --virtual-time-budget=8000 --screenshot="$out" "$url" 2>/dev/null
  echo "$out"
}

cmd_smoke() {
  cmd_login
  echo "== list (inactive must be absent)"; cmd_api GET /users/
  echo "== retrieve inactive by id";       cmd_api GET /users/4/
  local d1 d2 d3 d4
  d1=$(date -v+1d +%F); d2=$(date -v+2d +%F); d3=$(date -v+3d +%F); d4=$(date -v+4d +%F)
  echo "== generate plan"
  cmd_api POST /duties/generate/ "{\"dates\":[\"$d1\",\"$d2\",\"$d3\",\"$d4\"],\"people_per_day\":2}"
  echo "== screenshot"; cmd_screenshot
}

cmd_down() {
  pkill -f "manage.py runserver 8000" || true
  pkill -f "vite --port 5173" || true
}

"cmd_${1:-smoke}" "${@:2}"
