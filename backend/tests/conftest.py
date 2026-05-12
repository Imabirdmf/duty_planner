"""
Фикстуры для тестов приложения planner
"""

import os
import sys
from datetime import timedelta

import pytest

current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)
backend_dir = os.path.dirname(tests_dir)
root_dir = os.path.dirname(backend_dir)

if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.core.settings.local")

import django

django.setup()

from django.utils import timezone
from planner.models import DaysOff, Duty, DutyAssignment, Staff
from accounts.models import User, Invitation


@pytest.fixture
def api_client():
    """API client for testing"""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def auth_user(db):
    """Creates an authenticated User (for auth tests)"""
    return User.objects.create_user(email="auth@example.com", password="testpass123")


@pytest.fixture
def admin_user(db):
    """Creates an admin User"""
    return User.objects.create_superuser(
        email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def authenticated_client(api_client, auth_user):
    """API client with authenticated user"""
    api_client.force_authenticate(user=auth_user)
    return api_client


@pytest.fixture
def staff_user(db):
    return Staff.objects.create(
        first_name="Иван", last_name="Иванов", email="ivan@example.com", priority=0
    )


@pytest.fixture
def staff_users(db):
    users = [
        Staff.objects.create(
            first_name="Петр", last_name="Петров", email="petr@example.com", priority=1
        ),
        Staff.objects.create(
            first_name="Сидор",
            last_name="Сидоров",
            email="sidor@example.com",
            priority=2,
        ),
        Staff.objects.create(
            first_name="Мария",
            last_name="Иванова",
            email="maria@example.com",
            priority=0,
        ),
        Staff.objects.create(
            first_name="Анна", last_name="Петрова", email="anna@example.com", priority=1
        ),
    ]
    return users


@pytest.fixture
def today():
    return timezone.localdate()


@pytest.fixture
def tomorrow(today):
    return today + timedelta(days=1)


@pytest.fixture
def yesterday(today):
    return today - timedelta(days=1)


@pytest.fixture
def future_date(today):
    return today + timedelta(days=7)


@pytest.fixture
def date_range(today):
    start = today + timedelta(days=1)
    end = start + timedelta(days=6)
    return {
        "start": start,
        "end": end,
        "dates": [start + timedelta(days=i) for i in range(7)],
    }


@pytest.fixture
def duty_day(db, tomorrow):
    return Duty.objects.create(date=tomorrow)


@pytest.fixture
def duty_days(db, date_range):
    duties = [Duty.objects.create(date=d) for d in date_range["dates"]]
    return duties


@pytest.fixture
def day_off(db, staff_user, tomorrow):
    return DaysOff.objects.create(user=staff_user, date=tomorrow)


@pytest.fixture
def days_off_multiple(db, staff_users, date_range):
    days_off = [
        DaysOff.objects.create(user=staff_users[0], date=date_range["dates"][0]),
        DaysOff.objects.create(user=staff_users[1], date=date_range["dates"][1]),
        DaysOff.objects.create(user=staff_users[0], date=date_range["dates"][3]),
    ]
    return days_off


@pytest.fixture
def duty_assignment(db, staff_user, duty_day):
    return DutyAssignment.objects.create(user=staff_user, duty=duty_day)


@pytest.fixture
def duty_assignments(db, staff_users, duty_days):
    assignments = [
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0]),
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_days[0]),
        DutyAssignment.objects.create(user=staff_users[2], duty=duty_days[1]),
        DutyAssignment.objects.create(user=staff_users[3], duty=duty_days[1]),
    ]
    return assignments


@pytest.fixture
def duty_with_assignments(db, staff_users, duty_day):
    assignments = [
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_day),
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_day),
    ]
    return {
        "duty": duty_day,
        "assignments": assignments,
        "users": [staff_users[0], staff_users[1]],
    }


@pytest.fixture
def jira_env_vars(monkeypatch):
    """Set up Jira environment variables for testing"""
    monkeypatch.setenv("JIRA_BASE_URL", "https://test.atlassian.net")
    monkeypatch.setenv("JIRA_PROJECT_KEY", "TEST")
    monkeypatch.setenv("JIRA_PARENT_ISSUE_KEY", "TEST-123")
    monkeypatch.setenv("JIRA_EMAIL", "test@example.com")
    monkeypatch.setenv("JIRA_API_TOKEN", "test-token")


@pytest.fixture
def staff_with_jira(db):
    """Create staff member with Jira IDs"""
    return Staff.objects.create(
        first_name="Jira",
        last_name="User",
        email="jira@example.com",
        jira_team_id="team-123",
        jira_account_id="acc-456",
    )


@pytest.fixture
def mock_jira_service():
    """Mock JiraService for testing"""
    from unittest.mock import Mock
    from common_app.services.jira import JiraService

    jira = Mock(spec=JiraService)
    jira.create_issue.return_value = "TEST-789"
    return jira
