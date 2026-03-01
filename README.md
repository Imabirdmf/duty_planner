##### Current build status

[![Python CI](https://github.com/Imabirdmf/duty_planner/actions/workflows/ci.yaml/badge.svg)](https://github.com/Imabirdmf/duty_planner/actions/workflows/ci.yaml)

##### SonarQube

[![Quality gate](https://sonarcloud.io/api/project_badges/quality_gate?project=Imabirdmf_duty_planner)](https://sonarcloud.io/summary/new_code?id=Imabirdmf_duty_planner)

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

## Features

- 📅 **Intelligent Scheduling**: Automatic duty generation using priority-based queue algorithm
- 👥 **Staff Management**: Track staff availability with priority balancing
- 🗓️ **Days Off Management**: Register and manage staff days off
- 📊 **Assignment Tracking**: Create, update, and manage duty assignments
- 🔄 **Availability Checking**: Prevents consecutive assignments and respects days off
- ✅ **Comprehensive Testing**: ~230 tests covering all application layers
- 🐳 **Containerized**: Full Docker support for easy deployment
- 📈 **Code Quality**: Integrated SonarQube analysis

## Application Architecture
```bash
Views (API Endpoints)
    ↓
Services (Business Logic)
    ├── ManageAssignments - CRUD operations for assignments
    ├── Planner - Schedule generation algorithm
    └── StaffAvailability - Availability checking
    ↓
Repositories (Data Access)
    ├── StaffRepository
    ├── DutyRepository
    ├── DaysOffRepository
    └── DutyAssignmentRepository
    ↓
Models (Django ORM)
```

## Key Services
### Planner Service
Generates optimal duty schedules using a priority-based queue algorithm. Respects availability constraints and prevents consecutive assignments.

### ManageAssignments Service
Handles all CRUD operations for duty assignments with atomic transactions and automatic priority updates.

### StaffAvailability Service
Checks staff availability considering days off, current assignments, and previous duties to prevent consecutive scheduling.


## Getting Started

### Prerequisites

- Python ≥3.13
- Node.js & npm
- Docker & Docker Compose (optional)

### Installation

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

