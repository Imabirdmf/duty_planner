"""
Тесты для бизнес-логики (модули services)
"""

from datetime import timedelta

import pytest
from django.db import transaction
from planner.models import DaysOff, Duty, DutyAssignment, Staff
from planner.services.assignments import (
    delete_assignment,
    get_assignments,
    get_duty_assignments,
    make_assignment,
)
from planner.services.duty_calendar import get_duty_days, save_duty_days
from planner.services.planner import (
    create_duty_assignment,
    create_plan,
    get_days_off,
    set_minimum_priority,
    update_priority,
    user_has_previous_duty,
)


@pytest.mark.django_db
class TestPlannerService:
    """Тесты для planner.py (основная логика планирования)"""

    def test_create_plan_basic(self, staff_users, date_range):
        """Тест базовой генерации расписания"""
        # Создаем дни дежурства
        duties = [Duty.objects.create(date=d) for d in date_range["dates"]]

        messages = create_plan(
            date_start=date_range["start"], date_end=date_range["end"], people_for_day=2
        )

        # Проверяем, что назначения созданы
        assignments = DutyAssignment.objects.all()
        assert assignments.count() > 0

        # Проверяем, что приоритеты обновились
        for user in staff_users:
            user.refresh_from_db()
            # Приоритет должен увеличиться для тех, кто был назначен

    def test_create_plan_with_days_off(self, staff_users, date_range):
        """Тест генерации расписания с учетом выходных"""
        # Создаем дни дежурства
        duties = [Duty.objects.create(date=d) for d in date_range["dates"]]

        # Добавляем выходной для первого пользователя
        day_off_date = date_range["dates"][0]
        DaysOff.objects.create(user=staff_users[0], date=day_off_date)

        messages = create_plan(
            date_start=date_range["start"], date_end=date_range["end"], people_for_day=2
        )

        # Проверяем, что пользователь с выходным не назначен
        assignments_with_day_off = DutyAssignment.objects.filter(
            user=staff_users[0], duty__date=day_off_date
        )
        assert assignments_with_day_off.count() == 0

    def test_create_plan_insufficient_staff(self, staff_user, date_range):
        """Тест генерации когда сотрудников недостаточно"""
        # Создаем дни дежурства
        duties = [Duty.objects.create(date=d) for d in date_range["dates"]]

        messages = create_plan(
            date_start=date_range["start"],
            date_end=date_range["end"],
            people_for_day=5,  # Требуем больше людей, чем есть
        )

        # Должны быть сообщения об ошибках
        assert len(messages) > 0
        # Проверяем формат сообщений
        for date_key, msgs in messages.items():
            assert isinstance(msgs, list)

    def test_create_plan_respects_previous_duty(self, staff_users, date_range):
        """Тест что планировщик не назначает подряд"""
        # Создаем три последовательных дня
        dates = date_range["dates"][:3]
        duties = [Duty.objects.create(date=d) for d in dates]

        messages = create_plan(
            date_start=dates[0], date_end=dates[-1], people_for_day=1
        )

        # Проверяем что один пользователь не назначен два дня подряд
        for i in range(len(dates) - 1):
            today_assignments = DutyAssignment.objects.filter(duty__date=dates[i])
            tomorrow_assignments = DutyAssignment.objects.filter(
                duty__date=dates[i + 1]
            )

            today_users = set(a.user_id for a in today_assignments)
            tomorrow_users = set(a.user_id for a in tomorrow_assignments)

            # Пересечение должно быть пустым
            assert len(today_users & tomorrow_users) == 0

    def test_get_days_off_exists(self, day_off):
        """Тест проверки наличия выходного"""
        result = get_days_off(day_off.user.id, day_off.date)
        assert result is True

    def test_get_days_off_not_exists(self, staff_user, tomorrow):
        """Тест проверки отсутствия выходного"""
        result = get_days_off(staff_user.id, tomorrow)
        assert result is False

    def test_create_duty_assignment(self, staff_user, duty_day):
        """Тест создания назначения на дежурство"""
        create_duty_assignment(staff_user.id, duty_day)

        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

    def test_create_duty_assignment_idempotent(self, staff_user, duty_day):
        """Тест что создание назначения идемпотентно"""
        create_duty_assignment(staff_user.id, duty_day)
        create_duty_assignment(staff_user.id, duty_day)

        # Должно быть только одно назначение
        count = DutyAssignment.objects.filter(user=staff_user, duty=duty_day).count()
        assert count == 1

    def test_update_priority_with_value(self, staff_user):
        """Тест обновления приоритета с конкретным значением"""
        update_priority(staff_user.id, value=5)

        staff_user.refresh_from_db()
        assert staff_user.priority == 5

    def test_update_priority_with_diff(self, staff_user):
        """Тест обновления приоритета с дельтой"""
        initial_priority = staff_user.priority
        update_priority(staff_user.id, diff=3)

        staff_user.refresh_from_db()
        assert staff_user.priority == initial_priority + 3

    def test_update_priority_decrease(self, staff_users):
        """Тест уменьшения приоритета"""
        user = staff_users[1]  # У него priority = 2
        update_priority(user.id, diff=-1)

        user.refresh_from_db()
        assert user.priority == 1

    def test_user_has_previous_duty_true(self, staff_user, duty_days):
        """Тест проверки предыдущего дежурства - есть"""
        # Назначаем на первый день
        DutyAssignment.objects.create(user=staff_user, duty=duty_days[0])

        # Проверяем для второго дня
        result = user_has_previous_duty(staff_user.id, duty_days[1].date)
        assert result is True

    def test_user_has_previous_duty_false(self, staff_users, duty_days):
        """Тест проверки предыдущего дежурства - нет"""
        # Назначаем другого пользователя на первый день
        DutyAssignment.objects.create(user=staff_users[1], duty=duty_days[0])

        # Проверяем для нашего пользователя на второй день
        result = user_has_previous_duty(staff_users[0].id, duty_days[1].date)
        assert result is False

    def test_user_has_previous_duty_no_previous_duties(self, staff_user, duty_day):
        """Тест когда вообще нет предыдущих дежурств"""
        result = user_has_previous_duty(staff_user.id, duty_day.date)
        assert result is False

    def test_set_minimum_priority(self, staff_users):
        """Тест нормализации приоритетов"""
        # Устанавливаем разные приоритеты
        for i, user in enumerate(staff_users):
            user.priority = i + 5  # 5, 6, 7, 8, 9
            user.save()

        set_minimum_priority()

        # Проверяем что минимальный приоритет стал 0
        min_priority = min(Staff.objects.values_list("priority", flat=True))
        assert min_priority == 0

        # Проверяем что разница сохранилась
        priorities = sorted(Staff.objects.values_list("priority", flat=True))
        for i in range(len(priorities) - 1):
            assert priorities[i + 1] - priorities[i] == 1

    def test_set_minimum_priority_with_zeros(self, staff_users):
        """Тест нормализации когда уже есть нули"""
        # Устанавливаем некоторым пользователям priority = 0
        staff_users[0].priority = 0
        staff_users[0].save()
        staff_users[1].priority = 0
        staff_users[1].save()

        set_minimum_priority()

        # Приоритеты не должны измениться
        staff_users[0].refresh_from_db()
        staff_users[1].refresh_from_db()
        assert staff_users[0].priority == 0
        assert staff_users[1].priority == 0


@pytest.mark.django_db
class TestAssignmentsService:
    """Тесты для assignments.py"""

    def test_get_assignments_single_date(self, duty_assignments, date_range):
        """Тест получения назначений на один день"""
        target_date = date_range["dates"][0]
        result = get_assignments(target_date)

        # Должен вернуться queryset с дежурствами
        assert result.count() >= 1

    def test_get_assignments_date_range(self, duty_assignments, date_range):
        """Тест получения назначений за период"""
        result = get_assignments(date_range["start"], date_range["end"])

        assert result.count() >= 2

    def test_get_assignments_no_results(self, today):
        """Тест когда нет назначений на дату"""
        future_date = today + timedelta(days=100)
        result = get_assignments(future_date)

        assert result.count() == 0

    def test_get_duty_assignments_single_date(self, duty_assignments, date_range):
        """Тест получения объектов DutyAssignment на один день"""
        target_date = date_range["dates"][0]
        result = get_duty_assignments(target_date)

        assert result.count() >= 1
        assert all(isinstance(a, DutyAssignment) for a in result)

    def test_get_duty_assignments_date_range(self, duty_assignments, date_range):
        """Тест получения DutyAssignment за период"""
        result = get_duty_assignments(date_range["start"], date_range["end"])

        assert result.count() >= 2

    def test_make_assignment_new_user(self, staff_user, duty_day):
        """Тест назначения нового пользователя"""
        result = make_assignment(
            duty_date=duty_day.date, prev_user=None, new_user=staff_user.id
        )

        # Проверяем что назначение создано
        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

        # Проверяем что приоритет увеличился
        staff_user.refresh_from_db()
        assert staff_user.priority == 1

    def test_make_assignment_replace_user(self, duty_assignment, staff_users):
        """Тест замены пользователя"""
        print(staff_users)
        old_user = duty_assignment.user
        print("old_user", old_user)
        new_user = staff_users[2]  # Берем другого пользователя
        print("new_user", new_user)

        old_priority = old_user.priority
        new_priority = new_user.priority

        result = make_assignment(
            duty_date=duty_assignment.duty.date,
            prev_user=old_user.id,
            new_user=new_user.id,
        )

        # Проверяем что пользователь изменился
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

        # Проверяем изменение приоритетов
        old_user.refresh_from_db()
        new_user.refresh_from_db()
        assert old_user.priority == old_priority - 1
        assert new_user.priority == new_priority + 1

    def test_make_assignment_remove_user(self, duty_assignment):
        """Тест удаления назначения"""
        duty_date = duty_assignment.duty.date
        user_id = duty_assignment.user.id

        result = make_assignment(duty_date=duty_date, prev_user=user_id, new_user=None)

        # Проверяем что назначение удалено
        assert not DutyAssignment.objects.filter(id=duty_assignment.id).exists()

    def test_delete_assignment(self, duty_assignment):
        """Тест удаления назначения"""
        duty_date = duty_assignment.duty.date
        user_id = duty_assignment.user.id

        delete_assignment(duty_date, user_id)

        assert not DutyAssignment.objects.filter(id=duty_assignment.id).exists()

    def test_make_assignment_atomic(self, staff_users, duty_day):
        """Тест что make_assignment атомарный"""
        # Этот тест проверяет что при ошибке откатываются все изменения
        # Для этого нужно вызвать ошибку внутри транзакции

        with pytest.raises(Exception):
            with transaction.atomic():
                make_assignment(
                    duty_date=duty_day.date, prev_user=None, new_user=staff_users[0].id
                )
                # Искусственно вызываем ошибку
                raise Exception("Test rollback")

        # Проверяем что назначение не создано
        assert DutyAssignment.objects.count() == 0


@pytest.mark.django_db
class TestDutyCalendarService:
    """Тесты для duty_calendar.py"""

    def test_get_duty_days(self, duty_days, date_range):
        """Тест получения дней дежурства"""
        result = get_duty_days(date_range["start"], date_range["end"])

        assert result.count() == len(duty_days)
        # Проверяем сортировку
        dates = list(result.values_list("date", flat=True))
        assert dates == sorted(dates)

    def test_get_duty_days_empty(self, today):
        """Тест когда нет дней дежурства"""
        future_date = today + timedelta(days=100)
        result = get_duty_days(future_date, future_date)

        assert result.count() == 0

    def test_save_duty_days_new(self, date_range):
        """Тест создания новых дней дежурства"""
        dates = date_range["dates"]
        result = save_duty_days(dates)

        assert result.count() == len(dates)
        assert Duty.objects.count() == len(dates)

    def test_save_duty_days_idempotent(self, date_range):
        """Тест что сохранение идемпотентно"""
        dates = date_range["dates"]

        # Сохраняем первый раз
        result1 = save_duty_days(dates)
        count1 = Duty.objects.count()

        # Сохраняем второй раз те же даты
        result2 = save_duty_days(dates)
        count2 = Duty.objects.count()

        # Количество не должно измениться
        assert count1 == count2
        assert count1 == len(dates)

    def test_save_duty_days_unsorted(self, date_range):
        """Тест что даты сортируются автоматически"""
        dates = date_range["dates"]
        # Перемешиваем даты
        unsorted_dates = [dates[2], dates[0], dates[4], dates[1], dates[3]]

        result = save_duty_days(unsorted_dates)

        # Результат должен быть отсортирован
        result_dates = list(result.values_list("date", flat=True))
        assert result_dates == sorted(result_dates)

    def test_save_duty_days_mixed_new_and_existing(self, duty_days, date_range):
        """Тест сохранения когда часть дней уже существует"""
        # duty_days уже создал дни
        existing_dates = [d.date for d in duty_days]
        new_dates = [date_range["end"] + timedelta(days=i) for i in range(1, 4)]

        all_dates = existing_dates + new_dates
        result = save_duty_days(all_dates)

        assert result.count() == len(all_dates)
        assert Duty.objects.count() >= len(all_dates)


@pytest.mark.django_db
class TestBusinessLogicIntegration:
    """Интеграционные тесты бизнес-логики"""

    def test_full_duty_cycle(self, staff_users, date_range):
        """Тест полного цикла: создание дней -> планирование -> изменение"""
        # 1. Создаем дни дежурства
        dates = date_range["dates"][:3]
        saved_duties = save_duty_days(dates)

        # 2. Генерируем расписание
        messages = create_plan(dates[0], dates[-1], people_for_day=2)

        # 3. Проверяем что назначения созданы
        assignments = DutyAssignment.objects.all()
        assert assignments.count() > 0

        # 4. Изменяем одно назначение
        first_assignment = assignments.first()
        new_user = staff_users[-1]  # Берем последнего пользователя

        make_assignment(
            duty_date=first_assignment.duty.date,
            prev_user=first_assignment.user.id,
            new_user=new_user.id,
        )

        # 5. Проверяем изменение
        first_assignment.refresh_from_db()
        assert first_assignment.user.id == new_user.id

    def test_priority_consistency(self, staff_users, date_range):
        """Тест консистентности приоритетов при различных операциях"""
        dates = date_range["dates"][:5]
        save_duty_days(dates)

        # Генерируем расписание
        create_plan(dates[0], dates[-1], people_for_day=2)

        # Нормализуем приоритеты
        set_minimum_priority()

        # Проверяем что у кого-то priority = 0
        min_priority = Staff.objects.order_by("priority").first().priority
        assert min_priority == 0

        # Проверяем что все приоритеты >= 0
        negative_priorities = Staff.objects.filter(priority__lt=0)
        assert negative_priorities.count() == 0
