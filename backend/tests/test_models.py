"""
Тесты для моделей Django
"""

import pytest
from django.db import IntegrityError
from planner.models import DaysOff, Duty, DutyAssignment, Staff


@pytest.mark.django_db
class TestStaffModel:
    """Тесты для модели Staff"""

    def test_create_staff(self):
        """Тест создания сотрудника"""
        staff = Staff.objects.create(
            first_name="Иван", last_name="Иванов", email="ivan@example.com"
        )

        assert staff.id is not None
        assert staff.first_name == "Иван"
        assert staff.last_name == "Иванов"
        assert staff.email == "ivan@example.com"
        assert staff.priority == 0  # default value

    def test_full_name_property(self, staff_user):
        """Тест свойства full_name"""
        assert staff_user.full_name == f"{staff_user.first_name} {staff_user.last_name}"

    def test_full_name_with_empty_last_name(self):
        """Тест full_name когда фамилия пустая"""
        staff = Staff.objects.create(
            first_name="Иван", last_name="", email="ivan@example.com"
        )

        assert staff.full_name == "Иван"

    def test_full_name_with_empty_first_name(self):
        """Тест full_name когда имя пустое"""
        staff = Staff.objects.create(
            first_name="", last_name="Иванов", email="ivan@example.com"
        )

        assert staff.full_name == "Иванов"

    def test_str_representation(self, staff_user):
        """Тест строкового представления"""
        assert str(staff_user) == staff_user.full_name

    def test_email_unique_constraint(self, staff_user):
        """Тест уникальности email"""
        with pytest.raises(IntegrityError):
            Staff.objects.create(
                first_name="Петр",
                last_name="Петров",
                email=staff_user.email,  # Дублирующийся email
            )

    def test_priority_default_value(self):
        """Тест значения приоритета по умолчанию"""
        staff = Staff.objects.create(
            first_name="Иван", last_name="Иванов", email="ivan@example.com"
        )

        assert staff.priority == 0

    def test_priority_custom_value(self):
        """Тест установки кастомного приоритета"""
        staff = Staff.objects.create(
            first_name="Иван", last_name="Иванов", email="ivan@example.com", priority=5
        )

        assert staff.priority == 5

    def test_update_staff(self, staff_user):
        """Тест обновления сотрудника"""
        staff_user.first_name = "Новое Имя"
        staff_user.priority = 10
        staff_user.save()

        staff_user.refresh_from_db()
        assert staff_user.first_name == "Новое Имя"
        assert staff_user.priority == 10

    def test_delete_staff(self, staff_user):
        """Тест удаления сотрудника"""
        staff_id = staff_user.id
        staff_user.delete()

        assert not Staff.objects.filter(id=staff_id).exists()


@pytest.mark.django_db
class TestDaysOffModel:
    """Тесты для модели DaysOff"""

    def test_create_day_off(self, staff_user, tomorrow):
        """Тест создания выходного дня"""
        day_off = DaysOff.objects.create(user=staff_user, date=tomorrow)

        assert day_off.id is not None
        assert day_off.user == staff_user
        assert day_off.date == tomorrow

    def test_str_representation(self, day_off):
        """Тест строкового представления"""
        expected = f"{day_off.date} - userid: {day_off.user.id}"
        assert str(day_off) == expected

    def test_unique_constraint(self, staff_user, tomorrow):
        """Тест уникальности (user, date)"""
        DaysOff.objects.create(user=staff_user, date=tomorrow)

        with pytest.raises(IntegrityError):
            DaysOff.objects.create(user=staff_user, date=tomorrow)

    def test_same_date_different_users(self, staff_users, tomorrow):
        """Тест что разные пользователи могут иметь выходной в один день"""
        day_off1 = DaysOff.objects.create(user=staff_users[0], date=tomorrow)
        day_off2 = DaysOff.objects.create(user=staff_users[1], date=tomorrow)

        assert day_off1.id != day_off2.id
        assert day_off1.date == day_off2.date

    def test_same_user_different_dates(self, staff_user, tomorrow, future_date):
        """Тест что один пользователь может иметь несколько выходных"""
        day_off1 = DaysOff.objects.create(user=staff_user, date=tomorrow)
        day_off2 = DaysOff.objects.create(user=staff_user, date=future_date)

        assert day_off1.id != day_off2.id
        assert DaysOff.objects.filter(user=staff_user).count() == 2

    def test_cascade_delete_on_user_delete(self, day_off):
        """Тест каскадного удаления при удалении пользователя"""
        user = day_off.user
        day_off_id = day_off.id

        user.delete()

        assert not DaysOff.objects.filter(id=day_off_id).exists()

    def test_date_index(self, day_off):
        """Тест что поле date индексировано"""
        # Это проверяется через модель, индекс должен быть определен
        field = DaysOff._meta.get_field("date")
        assert field.db_index is True


@pytest.mark.django_db
class TestDutyModel:
    """Тесты для модели Duty"""

    def test_create_duty(self, tomorrow):
        """Тест создания дежурства"""
        duty = Duty.objects.create(date=tomorrow)

        assert duty.id is not None
        assert duty.date == tomorrow

    def test_str_representation(self, duty_day):
        """Тест строкового представления"""
        assert str(duty_day) == str(duty_day.date)

    def test_date_unique_constraint(self, tomorrow):
        """Тест уникальности даты"""
        Duty.objects.create(date=tomorrow)

        with pytest.raises(IntegrityError):
            Duty.objects.create(date=tomorrow)

    def test_date_index(self, duty_day):
        """Тест что поле date индексировано и уникально"""
        field = Duty._meta.get_field("date")
        assert field.db_index is True
        assert field.unique is True

    def test_bulk_update_or_create_manager(self):
        """Тест что используется кастомный менеджер"""
        # Проверяем что менеджер доступен
        assert hasattr(Duty.objects, "bulk_update_or_create")

    def test_delete_duty(self, duty_day):
        """Тест удаления дежурства"""
        duty_id = duty_day.id
        duty_day.delete()

        assert not Duty.objects.filter(id=duty_id).exists()


@pytest.mark.django_db
class TestDutyAssignmentModel:
    """Тесты для модели DutyAssignment"""

    def test_create_duty_assignment(self, staff_user, duty_day):
        """Тест создания назначения"""
        assignment = DutyAssignment.objects.create(user=staff_user, duty=duty_day)

        assert assignment.id is not None
        assert assignment.user == staff_user
        assert assignment.duty == duty_day

    def test_unique_constraint(self, staff_user, duty_day):
        """Тест уникальности (user, duty)"""
        DutyAssignment.objects.create(user=staff_user, duty=duty_day)

        with pytest.raises(IntegrityError):
            DutyAssignment.objects.create(user=staff_user, duty=duty_day)

    def test_same_duty_different_users(self, staff_users, duty_day):
        """Тест что разные пользователи могут быть назначены на одно дежурство"""
        assignment1 = DutyAssignment.objects.create(user=staff_users[0], duty=duty_day)
        assignment2 = DutyAssignment.objects.create(user=staff_users[1], duty=duty_day)

        assert assignment1.id != assignment2.id
        assert assignment1.duty == assignment2.duty
        assert DutyAssignment.objects.filter(duty=duty_day).count() == 2

    def test_same_user_different_duties(self, staff_user, duty_days):
        """Тест что один пользователь может быть назначен на разные дежурства"""
        assignment1 = DutyAssignment.objects.create(user=staff_user, duty=duty_days[0])
        assignment2 = DutyAssignment.objects.create(user=staff_user, duty=duty_days[1])

        assert assignment1.id != assignment2.id
        assert DutyAssignment.objects.filter(user=staff_user).count() == 2

    def test_cascade_delete_on_user_delete(self, duty_assignment):
        """Тест каскадного удаления при удалении пользователя"""
        user = duty_assignment.user
        assignment_id = duty_assignment.id

        user.delete()

        assert not DutyAssignment.objects.filter(id=assignment_id).exists()

    def test_cascade_delete_on_duty_delete(self, duty_assignment):
        """Тест каскадного удаления при удалении дежурства"""
        duty = duty_assignment.duty
        assignment_id = duty_assignment.id

        duty.delete()

        assert not DutyAssignment.objects.filter(id=assignment_id).exists()

    def test_bulk_update_or_create_manager(self):
        """Тест что используется кастомный менеджер"""
        assert hasattr(DutyAssignment.objects, "bulk_update_or_create")

    def test_related_name_from_duty(self, duty_with_assignments):
        """Тест обратной связи от Duty к DutyAssignment"""
        duty = duty_with_assignments["duty"]
        assignments = duty.dutyassignment_set.all()

        assert assignments.count() == 2
        assert all(a.duty == duty for a in assignments)

    def test_related_name_from_user(self, staff_user, duty_days):
        """Тест обратной связи от User к DutyAssignment"""
        # Создаем несколько назначений для пользователя
        DutyAssignment.objects.create(user=staff_user, duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_user, duty=duty_days[1])

        assignments = staff_user.dutyassignment_set.all()

        assert assignments.count() == 2
        assert all(a.user == staff_user for a in assignments)


@pytest.mark.django_db
class TestModelRelationships:
    """Тесты связей между моделями"""

    def test_staff_to_days_off_relationship(self, staff_user, tomorrow, future_date):
        """Тест связи Staff -> DaysOff"""
        DaysOff.objects.create(user=staff_user, date=tomorrow)
        DaysOff.objects.create(user=staff_user, date=future_date)

        days_off = staff_user.daysoff_set.all()
        assert days_off.count() == 2

    def test_staff_to_duty_assignment_relationship(self, staff_user, duty_days):
        """Тест связи Staff -> DutyAssignment"""
        DutyAssignment.objects.create(user=staff_user, duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_user, duty=duty_days[1])

        assignments = staff_user.dutyassignment_set.all()
        assert assignments.count() == 2

    def test_duty_to_assignment_relationship(self, duty_day, staff_users):
        """Тест связи Duty -> DutyAssignment"""
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_day)
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_day)

        assignments = duty_day.dutyassignment_set.all()
        assert assignments.count() == 2

    def test_complex_relationship_query(self, staff_users, duty_days):
        """Тест сложного запроса через связи"""
        # Создаем назначения
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_days[0])
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[1])

        # Получаем все дежурства первого пользователя
        user_duties = Duty.objects.filter(
            dutyassignment__user=staff_users[0]
        ).distinct()

        assert user_duties.count() == 2

        # Получаем всех пользователей на первом дежурстве
        duty_users = Staff.objects.filter(dutyassignment__duty=duty_days[0]).distinct()

        assert duty_users.count() == 2
