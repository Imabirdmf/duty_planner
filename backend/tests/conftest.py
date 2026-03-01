"""
Фикстуры для тестов приложения planner
"""

import pytest
import sys
import os
from datetime import date, timedelta

# Определяем корневую директорию проекта
current_file = os.path.abspath(__file__)
tests_dir = os.path.dirname(current_file)  # backend/tests/
backend_dir = os.path.dirname(tests_dir)  # backend/
root_dir = os.path.dirname(backend_dir)  # корень проекта (где Makefile)

# Добавляем необходимые пути в PYTHONPATH
# Это нужно для импорта модулей Django
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# DJANGO_SETTINGS_MODULE должен быть установлен в pytest.ini
# Если по какой-то причине он не установлен, устанавливаем по умолчанию
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.core.local")

import django

django.setup()

from django.utils import timezone
from planner.models import Staff, DaysOff, Duty, DutyAssignment


@pytest.fixture
def api_client():
    """Клиент для API запросов"""
    from rest_framework.test import APIClient

    return APIClient()


@pytest.fixture
def staff_user(db):
    """Создает одного сотрудника"""
    return Staff.objects.create(
        first_name="Иван", last_name="Иванов", email="ivan@example.com", priority=0
    )


@pytest.fixture
def staff_users(db):
    """Создает несколько сотрудников с разными приоритетами"""
    users = [
        Staff.objects.create(
            first_name="Иван2",
            last_name="Иванов2",
            email="ivan2@example.com",
            priority=0,
        ),
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
    """Возвращает сегодняшнюю дату"""
    return timezone.localdate()


@pytest.fixture
def tomorrow(today):
    """Возвращает завтрашнюю дату"""
    return today + timedelta(days=1)


@pytest.fixture
def yesterday(today):
    """Возвращает вчерашнюю дату"""
    return today - timedelta(days=1)


@pytest.fixture
def future_date(today):
    """Возвращает дату через 7 дней"""
    return today + timedelta(days=7)


@pytest.fixture
def date_range(today):
    """Возвращает диапазон дат на неделю вперед"""
    start = today + timedelta(days=1)
    end = start + timedelta(days=6)
    return {
        "start": start,
        "end": end,
        "dates": [start + timedelta(days=i) for i in range(7)],
    }


@pytest.fixture
def duty_day(db, tomorrow):
    """Создает один день дежурства"""
    return Duty.objects.create(date=tomorrow)


@pytest.fixture
def duty_days(db, date_range):
    """Создает несколько дней дежурства"""
    duties = [Duty.objects.create(date=d) for d in date_range["dates"]]
    return duties


@pytest.fixture
def day_off(db, staff_user, tomorrow):
    """Создает выходной день для сотрудника"""
    return DaysOff.objects.create(user=staff_user, date=tomorrow)


@pytest.fixture
def days_off_multiple(db, staff_users, date_range):
    """Создает несколько выходных для разных сотрудников"""
    days_off = [
        DaysOff.objects.create(user=staff_users[0], date=date_range["dates"][0]),
        DaysOff.objects.create(user=staff_users[1], date=date_range["dates"][1]),
        DaysOff.objects.create(user=staff_users[0], date=date_range["dates"][3]),
    ]
    return days_off


@pytest.fixture
def duty_assignment(db, staff_user, duty_day):
    """Создает назначение на дежурство"""
    return DutyAssignment.objects.create(user=staff_user, duty=duty_day)


@pytest.fixture
def duty_assignments(db, staff_users, duty_days):
    """Создает несколько назначений на дежурства"""
    assignments = [
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0]),
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_days[0]),
        DutyAssignment.objects.create(user=staff_users[2], duty=duty_days[1]),
        DutyAssignment.objects.create(user=staff_users[3], duty=duty_days[1]),
    ]
    return assignments


@pytest.fixture
def duty_with_assignments(db, staff_users, duty_day):
    """Создает дежурство с двумя назначенными сотрудниками"""
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
def authenticated_client(api_client, staff_user):
    """
    API клиент с аутентифицированным пользователем.
    Используйте если у вас есть authentication в API.
    """
    # Раскомментируйте и настройте если используете authentication:
    # api_client.force_authenticate(user=staff_user)
    return api_client
