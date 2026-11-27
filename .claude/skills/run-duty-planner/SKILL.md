---
name: run-duty-planner
description: Run, start, launch, smoke-test or screenshot DutyPlanner locally (Django REST API on :8000 + React/Vite frontend on :5173) against a throwaway SQLite DB with seeded staff; call API endpoints as a logged-in admin; verify backend changes end to end in the real app.
---

# Run DutyPlanner locally

Driven by `.claude/skills/run-duty-planner/driver.sh` (paths are relative to the
repo root). It starts the Django API and the Vite dev server against a fresh
SQLite DB in `.run-local/` (gitignored), seeds an admin plus 4 staff (3 active,
1 inactive — «Глеб Неактивный», id 4), calls the API with `curl`, and takes
screenshots with headless Google Chrome. Verified on macOS (Apple Silicon).

## Prerequisites

```bash
brew install uv          # uv was missing on this machine; Python 3.13 is fetched by uv
```

Also needed and already present here: Node 24 + npm (via nvm), Google Chrome in
`/Applications` (override with `CHROME=...`). No Postgres / Docker needed.

## Run (agent path)

```bash
D=.claude/skills/run-duty-planner/driver.sh
$D up > /dev/null 2>&1   # fresh DB, migrate, seed, start :8000 and :5173 (do NOT pipe, see Gotchas)
$D smoke                 # login, list staff, get inactive by id, generate 4-day plan, screenshot
$D down                  # stop both servers
```

Smoke expectations: `/users/` lists Анна, Борис, Вера (no Глеб); `/users/4/`
returns Глеб; generated plan never contains Глеб and reports 2 days with 1 of 2
people. The screenshot lands in `.run-local/front.png` — open it with Read.

Ad-hoc calls (after `up`):

```bash
$D login                                   # stores JWT cookies in .run-local/cookies.txt
$D api GET /users/
$D api POST /duties/generate/ '{"dates":["2026-11-28"],"people_per_day":2}'
$D screenshot                              # or: $D screenshot <url> <out.png>
```

Run Django management commands against the same DB by exporting the same env
the driver uses, e.g. `DATABASE_URL=sqlite:///$PWD/.run-local/dev.sqlite3 uv run backend/manage.py shell`.

Admin login for the UI/API: `admin@example.com` / `admin-pass-123` (local DB only).

## Test

```bash
DATABASE_URL=sqlite:///$PWD/.run-local/test.sqlite3 SECRET_KEY=x FRONTEND_URL=http://localhost:5173 \
JIRA_BASE_URL=https://p.atlassian.net JIRA_EMAIL=p@example.com JIRA_API_TOKEN=p \
JIRA_PROJECT_KEY=P JIRA_PARENT_ISSUE_KEY=P-1 uv run pytest -q --create-db
make lint                # ruff + black + mypy, same as CI
```

## Gotchas

- **Never pipe `driver.sh up`** (`| tail`, `| head`): the background servers keep
  the pipe open and the command hangs forever even though both servers are up.
  Redirect to a file or `/dev/null` instead.
- `backend/.env` points `DATABASE_URL` at a local Postgres that isn't running. The
  driver exports `DATABASE_URL` (and CI-style placeholders for SECRET_KEY/JIRA_*)
  before Django starts; `load_dotenv` doesn't override existing env vars, so the
  `.env` value is ignored. `.env` also contains a commented-out *remote* DB URL —
  never point the driver at it.
- `uv sync` without `--python 3.13` picks Python 3.14; CI runs 3.13, so the
  driver pins 3.13.
- Router prefixes are not the model names: plans live under `/api/duties/...`
  (`generate`, `assign`, `list_assignments`), not `/api/assignments/`.
- Login is `POST /api/auth/login/` with `{"email","password"}`; auth is an
  HttpOnly JWT cookie (`auth-token`), so use the cookie jar, not a header.
- Write run artifacts inside the repo (`.run-local/`): agents may be denied reads
  of `/tmp`, so screenshots there can't be inspected.
- No `timeout` binary on macOS; `chromium-cli` isn't installed — the driver uses
  Chrome's own `--headless=new --screenshot`.

## Troubleshooting

- `command not found: uv` / `.venv/bin/python: no such file` → uv's Python was
  removed; `brew install uv`, `rm -rf .venv`, rerun `$D up`.
- `Not Found: /api/assignments/generate/` in `.run-local/backend.log` → use
  `/api/duties/generate/`.
- Port already in use / stale servers → `$D down`.
