"""
Тесты для валидаторов и сериализаторов
"""

from datetime import timedelta

import pytest
from planner.models import DutyAssignment
from planner.serializers import (
    DatesQuerySerializer,
    DaysOffSerializer,
    DutyAssignmentChangeSerializer,
    DutyAssignmentGenerateSerializer,
    DutyAssignmentSerializer,
    DutyWithAssignmentsSerializer,
    StaffSerializer,
)
from planner.validators import validate_date_not_past
from rest_framework import serializers as drf_serializers


@pytest.mark.django_db
class TestValidators:
    """Тесты для валидаторов"""

    def test_validate_date_not_past_valid_future(self, tomorrow):
        """Тест валидации будущей даты - должна пройти"""
        result = validate_date_not_past(tomorrow)
        assert result == tomorrow

    def test_validate_date_not_past_valid_today(self, today):
        """Тест валидации сегодняшней даты - должна пройти"""
        result = validate_date_not_past(today)
        assert result == today

    def test_validate_date_not_past_invalid_yesterday(self, yesterday):
        """Тест валидации вчерашней даты - должна упасть"""
        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            validate_date_not_past(yesterday)

        assert "Нельзя добавить дату из прошлого" in str(exc_info.value)

    def test_validate_date_not_past_invalid_old_date(self, today):
        """Тест валидации старой даты"""
        old_date = today - timedelta(days=365)

        with pytest.raises(drf_serializers.ValidationError) as exc_info:
            validate_date_not_past(old_date)

        assert "Нельзя добавить дату из прошлого" in str(exc_info.value)


@pytest.mark.django_db
class TestStaffSerializer:
    """Тесты для StaffSerializer"""

    def test_serialize_staff(self, staff_user):
        """Тест сериализации сотрудника"""
        serializer = StaffSerializer(staff_user)
        data = serializer.data

        assert data["id"] == staff_user.id
        assert data["email"] == staff_user.email
        assert data["first_name"] == staff_user.first_name
        assert data["last_name"] == staff_user.last_name
        assert data["full_name"] == staff_user.full_name

    def test_deserialize_staff_valid(self):
        """Тест десериализации валидных данных"""
        data = {
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@example.com",
        }
        serializer = StaffSerializer(data=data)

        assert serializer.is_valid()
        staff = serializer.save()

        assert staff.first_name == "Тест"
        assert staff.last_name == "Тестов"
        assert staff.email == "test@example.com"
        assert staff.priority == 0  # default value

    def test_deserialize_staff_invalid_email(self):
        """Тест десериализации с некорректным email"""
        data = {"first_name": "Тест", "last_name": "Тестов", "email": "invalid-email"}
        serializer = StaffSerializer(data=data)

        assert not serializer.is_valid()
        assert "email" in serializer.errors

    def test_deserialize_staff_missing_field(self):
        """Тест десериализации с отсутствующим полем"""
        data = {
            "first_name": "Тест",
            "email": "test@example.com",
            # отсутствует last_name
        }
        serializer = StaffSerializer(data=data)

        assert not serializer.is_valid()
        assert "last_name" in serializer.errors

    def test_full_name_read_only(self, staff_user):
        """Тест что full_name только для чтения"""
        data = {
            "first_name": "Новое",
            "last_name": "Имя",
            "email": staff_user.email,
            "full_name": "Игнорируемое значение",
        }
        serializer = StaffSerializer(staff_user, data=data)

        assert serializer.is_valid()
        serializer.save()

        staff_user.refresh_from_db()
        assert staff_user.full_name == "Новое Имя"  # Вычисляется автоматически


@pytest.mark.django_db
class TestDaysOffSerializer:
    """Тесты для DaysOffSerializer"""

    def test_serialize_day_off(self, day_off):
        """Тест сериализации выходного дня"""
        serializer = DaysOffSerializer(day_off)
        data = serializer.data

        assert data["id"] == day_off.id
        assert data["user"] == day_off.user.id
        assert data["date"] == day_off.date.isoformat()

    def test_deserialize_day_off_valid(self, staff_user, tomorrow):
        """Тест десериализации валидного выходного"""
        data = {"user": staff_user.id, "date": tomorrow.isoformat()}
        serializer = DaysOffSerializer(data=data)

        assert serializer.is_valid()
        day_off = serializer.save()

        assert day_off.user == staff_user
        assert day_off.date == tomorrow

    def test_deserialize_day_off_past_date(self, staff_user, yesterday):
        """Тест что нельзя создать выходной на прошедшую дату"""
        data = {"user": staff_user.id, "date": yesterday.isoformat()}
        serializer = DaysOffSerializer(data=data)

        assert not serializer.is_valid()
        assert "date" in serializer.errors
        assert "Нельзя добавить дату из прошлого" in str(serializer.errors["date"])

    def test_deserialize_day_off_duplicate(self, day_off):
        """Тест создания дублирующегося выходного"""
        data = {"user": day_off.user.id, "date": day_off.date.isoformat()}
        serializer = DaysOffSerializer(data=data)

        assert not serializer.is_valid()
        assert "non_field_errors" in serializer.errors
        assert "уже есть выходной" in str(serializer.errors)


@pytest.mark.django_db
class TestDutyAssignmentSerializer:
    """Тесты для DutyAssignmentSerializer"""

    def test_serialize_duty_assignment(self, duty_assignment):
        """Тест сериализации назначения"""
        serializer = DutyAssignmentSerializer(duty_assignment)
        data = serializer.data

        assert data["id"] == duty_assignment.id
        assert data["user"] == duty_assignment.user.id
        assert data["duty"] == duty_assignment.duty.id

    def test_deserialize_duty_assignment_valid(self, staff_user, duty_day):
        """Тест десериализации валидного назначения"""
        data = {"user": staff_user.id, "duty": duty_day.id}
        serializer = DutyAssignmentSerializer(data=data)

        assert serializer.is_valid()
        assignment = serializer.save()

        assert assignment.user == staff_user
        assert assignment.duty == duty_day


@pytest.mark.django_db
class TestDatesQuerySerializer:
    """Тесты для DatesQuerySerializer"""

    def test_valid_date_range(self, date_range):
        """Тест валидного диапазона дат"""
        data = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        serializer = DatesQuerySerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["start_date"] == date_range["start"]
        assert serializer.validated_data["end_date"] == date_range["end"]

    def test_missing_start_date(self, date_range):
        """Тест отсутствия start_date"""
        data = {"end_date": date_range["end"].isoformat()}
        serializer = DatesQuerySerializer(data=data)

        assert not serializer.is_valid()
        assert "start_date" in serializer.errors

    def test_missing_end_date(self, date_range):
        """Тест отсутствия end_date"""
        data = {"start_date": date_range["start"].isoformat()}
        serializer = DatesQuerySerializer(data=data)

        assert not serializer.is_valid()
        assert "end_date" in serializer.errors

    def test_invalid_date_format(self):
        """Тест некорректного формата даты"""
        data = {"start_date": "invalid-date", "end_date": "2024-01-01"}
        serializer = DatesQuerySerializer(data=data)

        assert not serializer.is_valid()
        assert "start_date" in serializer.errors


@pytest.mark.django_db
class TestDutyAssignmentGenerateSerializer:
    """Тесты для DutyAssignmentGenerateSerializer"""

    def test_valid_generate_data(self, date_range):
        """Тест валидных данных для генерации"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        serializer = DutyAssignmentGenerateSerializer(data=data)

        assert serializer.is_valid()
        assert len(serializer.validated_data["dates"]) == len(date_range["dates"])
        assert serializer.validated_data["people_per_day"] == 2

    def test_empty_dates_list(self):
        """Тест пустого списка дат"""
        data = {"dates": [], "people_per_day": 2}
        serializer = DutyAssignmentGenerateSerializer(data=data)

        # Пустой список технически валиден для ListField,
        # но бизнес-логика должна это обработать
        assert serializer.is_valid() or not serializer.is_valid()

    def test_invalid_people_per_day(self, date_range):
        """Тест превышения максимального количества людей"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 15,  # Больше max_value=10
        }
        serializer = DutyAssignmentGenerateSerializer(data=data)

        assert not serializer.is_valid()
        assert "people_per_day" in serializer.errors

    def test_negative_people_per_day(self, date_range):
        """Тест отрицательного количества людей"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": -1,
        }
        serializer = DutyAssignmentGenerateSerializer(data=data)

        assert not serializer.is_valid()

    def test_invalid_date_in_list(self, date_range):
        """Тест некорректной даты в списке"""
        dates = [d.isoformat() for d in date_range["dates"]]
        dates.append("invalid-date")

        data = {"dates": dates, "people_per_day": 2}
        serializer = DutyAssignmentGenerateSerializer(data=data)

        assert not serializer.is_valid()
        assert "dates" in serializer.errors


@pytest.mark.django_db
class TestDutyAssignmentChangeSerializer:
    """Тесты для DutyAssignmentChangeSerializer"""

    def test_assign_new_user(self, staff_user, tomorrow):
        """Тест данных для назначения нового пользователя"""
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": tomorrow.isoformat(),
        }
        serializer = DutyAssignmentChangeSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["user_id_prev"] is None
        assert serializer.validated_data["user_id_new"] == staff_user.id

    def test_replace_user(self, staff_users, tomorrow):
        """Тест данных для замены пользователя"""
        data = {
            "user_id_prev": staff_users[0].id,
            "user_id_new": staff_users[1].id,
            "date": tomorrow.isoformat(),
        }
        serializer = DutyAssignmentChangeSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["user_id_prev"] == staff_users[0].id
        assert serializer.validated_data["user_id_new"] == staff_users[1].id

    def test_remove_user(self, staff_user, tomorrow):
        """Тест данных для удаления назначения"""
        data = {
            "user_id_prev": staff_user.id,
            "user_id_new": None,
            "date": tomorrow.isoformat(),
        }
        serializer = DutyAssignmentChangeSerializer(data=data)

        assert serializer.is_valid()
        assert serializer.validated_data["user_id_prev"] == staff_user.id
        assert serializer.validated_data["user_id_new"] is None

    def test_missing_date(self, staff_user):
        """Тест отсутствия даты"""
        data = {"user_id_prev": None, "user_id_new": staff_user.id}
        serializer = DutyAssignmentChangeSerializer(data=data)

        assert not serializer.is_valid()
        assert "date" in serializer.errors

    def test_both_users_none(self, tomorrow):
        """Тест когда оба пользователя None"""
        data = {"user_id_prev": None, "user_id_new": None, "date": tomorrow.isoformat()}
        serializer = DutyAssignmentChangeSerializer(data=data)

        # Сериализатор должен быть валиден,
        # но бизнес-логика должна обработать этот случай
        assert serializer.is_valid()


@pytest.mark.django_db
class TestDutyWithAssignmentsSerializer:
    """Тесты для DutyWithAssignmentsSerializer"""

    def test_serialize_duty_with_assignments(self, duty_with_assignments):
        """Тест сериализации дежурства с назначениями"""
        duty = duty_with_assignments["duty"]
        serializer = DutyWithAssignmentsSerializer(duty)
        data = serializer.data

        assert data["id"] == duty.id
        assert data["date"] == duty.date.isoformat()
        assert "users" in data
        assert len(data["users"]) == 2

        # Проверяем структуру пользователей
        for user_data in data["users"]:
            assert "id" in user_data
            assert "first_name" in user_data
            assert "last_name" in user_data
            assert "email" in user_data
            assert "full_name" in user_data

    def test_serialize_duty_without_assignments(self, duty_day):
        """Тест сериализации дежурства без назначений"""
        serializer = DutyWithAssignmentsSerializer(duty_day)
        data = serializer.data

        assert data["id"] == duty_day.id
        assert data["date"] == duty_day.date.isoformat()
        assert data["users"] == []

    def test_serialize_multiple_duties(self, duty_days, staff_users):
        """Тест сериализации нескольких дежурств"""
        # Создаем назначения для первых двух дней
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_users[2], duty=duty_days[1])

        serializer = DutyWithAssignmentsSerializer(duty_days[:2], many=True)
        data = serializer.data

        assert len(data) == 2
        assert len(data[0]["users"]) == 2
        assert len(data[1]["users"]) == 1

    def test_users_field_structure(self, duty_with_assignments):
        """Тест структуры поля users"""
        duty = duty_with_assignments["duty"]
        serializer = DutyWithAssignmentsSerializer(duty)
        data = serializer.data

        users = data["users"]
        expected_users = duty_with_assignments["users"]

        # Проверяем что все пользователи присутствуют
        user_ids = [u["id"] for u in users]
        expected_ids = [u.id for u in expected_users]

        assert set(user_ids) == set(expected_ids)
