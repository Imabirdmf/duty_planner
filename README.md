# DutyPlanner

[![Python CI](https://github.com/Imabirdmf/duty_planner/actions/workflows/ci.yaml/badge.svg)](https://github.com/Imabirdmf/duty_planner/actions/workflows/ci.yaml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/quality_gate?project=Imabirdmf_duty_planner)](https://sonarcloud.io/summary/new_code?id=Imabirdmf_duty_planner)

A web application for automating staff duty scheduling. DutyPlanner generates optimal duty rosters, tracks staff availability, and syncs assignments directly to Jira — so you spend less time on spreadsheets and more time on actual work.

---

## Overview

Duty Planner is a full-stack web application designed to automate and manage staff duty scheduling. It uses intelligent algorithms to generate optimal duty schedules while respecting staff availability, preventing consecutive assignments, and balancing workload distribution using priority queuing.

**Tech Stack:**
- **Backend**: Python 78.3% (Django REST Framework)
- **Frontend**: React + Vite with JavaScript 19%
- **Styling**: CSS 2.2%
- **Database**: PostgreSQL
- **Containerization**: Docker & Docker Compose
- **Web Server**: Nginx + Gunicorn
- **Testing**: pytest with >85% coverage


## Key Services
### Planner Service
Generates optimal duty schedules using a priority-based queue algorithm. Respects availability constraints and prevents consecutive assignments.

### ManageAssignments Service
Handles all CRUD operations for duty assignments with atomic transactions and automatic priority updates.

### StaffAvailability Service
Checks staff availability considering days off, current assignments, and previous duties to prevent consecutive scheduling.

---

## What it does

- **Generates duty schedules automatically** — using a priority-based queue algorithm that balances workload fairly across the team
- **Respects constraints** — days off are taken into account, and no one gets scheduled for consecutive duties
- **Lets you adjust assignments manually** — swap people in and out for individual dates after generation
- **Syncs to Jira** — creates or updates Jira issues for duty assignments with one click
- **Invite-only access** — new users can only register via a unique invitation link, keeping the team list controlled

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | Django 6 + Django REST Framework |
| Frontend | React + Vite |
| Database | PostgreSQL |
| Auth | JWT via HttpOnly cookies (dj-rest-auth + simplejwt) |
| OAuth | Google OAuth 2.0 (domain-restricted) |
| Web server | Nginx + Gunicorn |
| Containerization | Docker + Docker Compose |
| CI | GitHub Actions |
| Code quality | SonarCloud |
| Package manager | uv |

---

## Project structure

```
duty_planner/
├── backend/
│   ├── accounts/          # Auth: registration, invitations, Google OAuth
│   ├── planner/           # Core domain: staff, duties, assignments, scheduling
│   │   ├── models.py
│   │   ├── views.py
│   │   ├── serializers.py
│   │   ├── repositories/  # Data access layer
│   │   └── services/      # Business logic layer
│   │       ├── assignments.py   # CRUD for assignments
│   │       ├── planner.py       # Schedule generation algorithm
│   │       └── availability.py  # Constraint checking
│   ├── common_app/
│   │   └── services/
│   │       └── jira.py    # Jira API integration
│   ├── core/
│   │   └── settings/      # base / local / production
│   └── tests/             # pytest test suite
├── frontend/              # React application
├── nginx/
│   └── nginx.conf
├── docker-compose.yml
├── Makefile
└── pyproject.toml
```

### Backend architecture

The backend follows a layered architecture — each layer has a single responsibility:

```
API Views (ViewSets)
    ↓
Services (business logic)
    ├── ManageAssignments   — CRUD operations, Jira sync
    ├── Planner             — schedule generation
    └── StaffAvailability   — constraint checking
    ↓
Repositories (database access)
    ├── StaffRepository
    ├── DutyRepository
    ├── DaysOffRepository
    └── DutyAssignmentRepository
    ↓
Django ORM / PostgreSQL
```

---

## Getting started

### Prerequisites

- Python ≥ 3.13
- Node.js ≥ 20 and npm
- Docker and Docker Compose (for the recommended setup)

- ## Deployment

The app is deployed on [Railway](https://railway.app/) with three separate services:

- **Backend** — Django + Gunicorn, built from `backend/Dockerfile.backend`
- **Frontend** — React + Nginx, built from `frontend/Dockerfile.frontend`; nginx proxies `/api/` and `/admin/` requests to the backend's internal Railway URL
- **Database** — managed PostgreSQL service

Key production settings:
- `DJANGO_SETTINGS_MODULE=core.settings.production`
- JWT cookies are set with `Secure=True` and `SameSite=None`
- Static files are served via WhiteNoise
---

[//]: # ()
[//]: # (## Contributing)

[//]: # ()
[//]: # (1. Fork the repository)

[//]: # (2. Create a feature branch: `git checkout -b feature/your-feature`)

[//]: # (3. Make your changes)

[//]: # (4. Run linting and tests: `make lint && make check`)

[//]: # (5. Open a pull request — CI will run automatically on push)

#### Using Docker Compose (Recommended)


```bash
# Clone the repository
git clone https://github.com/Imabirdmf/duty_planner.git
cd duty_planner

# Start all services
docker-compose up -d

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# Admin: http://localhost:8000/admin


### Option 1 — Docker Compose (recommended)

```bash
git clone https://github.com/Imabirdmf/duty_planner.git
cd duty_planner

# Create the backend env file (see Environment variables section below)
cp backend/.env.example backend/.env

docker-compose up -d
```

The app will be available at:
- Frontend: http://localhost:80
- Backend API: http://localhost:8000/api/
- Django admin: http://localhost:8000/admin/

### Option 2 — Local development (without Docker)

**Backend:**

```bash
# Install dependencies with uv
make install

# Set up the database
uv run backend/manage.py migrate

# Create a superuser
uv run backend/manage.py createsuperuser

# Start the dev server
uv run backend/manage.py runserver
```

**Frontend:**

```bash
cd frontend
npm install
npm run dev
```

---

## Environment variables

Create `backend/.env` with the following variables:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/planner
FRONTEND_URL=http://localhost:5173

# Google OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/google/callback/
GOOGLE_ALLOWED_DOMAIN=yourcompany.com   # restrict to one domain, or leave blank

# Jira integration (optional)
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=your@email.com
JIRA_API_TOKEN=your-api-token
JIRA_PROJECT_KEY=PROJ
JIRA_PARENT_ISSUE_KEY=PROJ-1
```

---

## API reference

All endpoints are prefixed with `/api/`.

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| POST | `/auth/registration/` | Register with invitation token | No |
| POST | `/auth/login/` | Login with email + password | No |
| POST | `/auth/logout/` | Logout | Yes |
| POST | `/auth/invite/` | Create an invitation link | Yes |
| POST | `/auth/google/` | Start Google OAuth flow | No |
| GET | `/auth/google/callback/` | Google OAuth callback | No |
| GET | `/api/users/` | List all staff | Yes |
| GET | `/api/duties/` | List duty assignments | Yes |
| POST | `/api/duties/generate/` | Generate duty schedule | Yes |
| POST | `/api/duties/assign/` | Reassign a duty slot | Yes |
| POST | `/api/duties/bulk_delete/` | Delete duty days | Yes |
| GET | `/api/days-off/` | List days off | Yes |
| POST | `/api/days-off/` | Add days off for staff | Yes |
| POST | `/api/jira/sync/` | Sync assignments to Jira | Yes |

---

## Development commands

All commands are run from the project root.

```bash
make install          # Install Python dependencies via uv
make check            # Run tests
make test-coverage    # Run tests with coverage report (coverage.xml)
make lint             # Run ruff + black + mypy
make format           # Auto-fix formatting issues
make migrations       # Generate new migrations
```

---

## Tests

Tests live in `backend/tests/` and cover all application layers:

```
backend/tests/
├── conftest.py                   # Shared fixtures
├── test_models.py
├── test_serializers.py
├── test_repositories.py
├── test_staff_availability.py
├── test_manage_assignments.py
├── test_planner.py
├── test_views.py
├── test_accounts.py
├── test_dj_rest_auth.py
├── test_jira_integration.py
└── test_integration.py
```

Run all tests:

```bash
make check
```

Run with coverage:

```bash
make test-coverage
```
