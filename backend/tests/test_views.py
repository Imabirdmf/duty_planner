"""
Тесты для view-функций (ViewSets)
"""

import pytest
from django.urls import reverse
from planner.models import DaysOff, Duty, DutyAssignment, Staff
from rest_framework import status


@pytest.mark.django_db
class TestStaffViewSet:
    """Тесты для StaffViewSet"""

    def test_list_staff(self, api_client, staff_users):
        """Тест получения списка сотрудников"""
        url = reverse("staff-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(staff_users)

    def test_create_staff(self, api_client):
        """Тест создания сотрудника"""
        url = reverse("staff-list")
        data = {
            "first_name": "Тест",
            "last_name": "Тестов",
            "email": "test@example.com",
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Тест"
        assert response.data["last_name"] == "Тестов"
        assert response.data["full_name"] == "Тест Тестов"
        assert Staff.objects.count() == 1

    def test_retrieve_staff(self, api_client, staff_user):
        """Тест получения конкретного сотрудника"""
        url = reverse("staff-detail", kwargs={"pk": staff_user.id})
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == staff_user.id
        assert response.data["email"] == staff_user.email
        assert response.data["full_name"] == staff_user.full_name

    def test_update_staff(self, api_client, staff_user):
        """Тест обновления сотрудника"""
        url = reverse("staff-detail", kwargs={"pk": staff_user.id})
        data = {
            "first_name": "Обновленный",
            "last_name": "Пользователь",
            "email": "updated@example.com",
        }
        response = api_client.put(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Обновленный"
        assert response.data["last_name"] == "Пользователь"

        staff_user.refresh_from_db()
        assert staff_user.first_name == "Обновленный"

    def test_delete_staff(self, api_client, staff_user):
        """Тест удаления сотрудника"""
        url = reverse("staff-detail", kwargs={"pk": staff_user.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Staff.objects.count() == 0

    def test_create_staff_duplicate_email(self, api_client, staff_user):
        """Тест создания сотрудника с дублирующимся email"""
        url = reverse("staff-list")
        data = {
            "first_name": "Другой",
            "last_name": "Человек",
            "email": staff_user.email,  # дублирующийся email
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDaysOffViewSet:
    """Тесты для DaysOffViewSet"""

    def test_list_days_off(self, api_client, days_off_multiple):
        """Тест получения списка выходных"""
        url = reverse("daysoff-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(days_off_multiple)

    def test_list_days_off_with_date_filter(
        self, api_client, days_off_multiple, date_range
    ):
        """Тест получения выходных с фильтрацией по датам"""
        url = reverse("daysoff-list")
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK

    def test_create_day_off(self, api_client, staff_user, tomorrow):
        """Тест создания выходного дня"""
        url = reverse("daysoff-list")
        data = {"user": staff_user.id, "date": tomorrow.isoformat()}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DaysOff.objects.count() == 1

    def test_create_day_off_past_date(self, api_client, staff_user, yesterday):
        """Тест создания выходного на прошедшую дату - должно быть запрещено"""
        url = reverse("daysoff-list")
        data = {"user": staff_user.id, "date": yesterday.isoformat()}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Нельзя добавить дату из прошлого" in str(response.data)

    def test_create_duplicate_day_off(self, api_client, day_off):
        """Тест создания дублирующегося выходного"""
        url = reverse("daysoff-list")
        data = {"user": day_off.user.id, "date": day_off.date.isoformat()}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "уже есть выходной" in str(response.data)

    def test_delete_day_off(self, api_client, day_off):
        """Тест удаления выходного дня"""
        url = reverse("daysoff-detail", kwargs={"pk": day_off.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DaysOff.objects.count() == 0


@pytest.mark.django_db
class TestDutyAssignmentViewSet:
    """Тесты для DutyAssignmentViewSet"""

    def test_list_assignments_action(self, api_client, duty_assignments, date_range):
        """Тест получения списка назначений через action list_assignments"""
        url = reverse("dutyassignment-list-assignments")
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        response = api_client.get(url, params)

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert len(response.data["data"]) > 0

    def test_list_assignments_missing_params(self, api_client):
        """Тест списка назначений без обязательных параметров"""
        url = reverse("dutyassignment-list-assignments")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_duty_plan(self, api_client, staff_users, date_range):
        """Тест генерации расписания дежурств"""
        url = reverse("dutyassignment-generate")
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "errors" in response.data

        # Проверяем, что созданы дежурства
        assert Duty.objects.count() == len(date_range["dates"])

    def test_generate_duty_plan_with_insufficient_staff(
        self, api_client, staff_user, date_range
    ):
        """Тест генерации расписания с недостаточным количеством сотрудников"""
        url = reverse("dutyassignment-generate")
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 5,  # Больше чем сотрудников
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        # Должны быть сообщения об ошибках
        assert len(response.data.get("errors", {})) > 0

    def test_generate_duty_plan_invalid_people_per_day(self, api_client, date_range):
        """Тест генерации с некорректным количеством людей на день"""
        url = reverse("dutyassignment-generate")
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 15,  # Больше максимального (10)
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_new_user_to_duty(
        self, api_client, staff_user, duty_day, date_range
    ):
        """Тест назначения нового пользователя на дежурство"""
        url = reverse("dutyassignment-assign")
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = api_client.post(url, data, params=params, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data

        # Проверяем, что назначение создано
        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

    def test_change_duty_assignment(
        self, api_client, duty_assignment, staff_users, date_range
    ):
        """Тест изменения назначения (замена пользователя)"""
        url = reverse("dutyassignment-assign")
        new_user = staff_users[1]  # Выбираем другого пользователя
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": duty_assignment.user.id,
            "user_id_new": new_user.id,
            "date": duty_assignment.duty.date.isoformat(),
        }
        response = api_client.post(url, data, params=params, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Проверяем, что назначение изменено
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

    def test_remove_duty_assignment(self, api_client, duty_assignment, date_range):
        """Тест удаления назначения"""
        url = reverse("dutyassignment-assign")
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": duty_assignment.user.id,
            "user_id_new": None,
            "date": duty_assignment.duty.date.isoformat(),
        }
        response = api_client.post(url, data, params=params, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Проверяем, что назначение удалено
        assert not DutyAssignment.objects.filter(id=duty_assignment.id).exists()

    def test_assign_missing_query_params(self, api_client, staff_user, duty_day):
        """Тест назначения без query параметров"""
        url = reverse("dutyassignment-assign")
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_duty_assignment(self, api_client, staff_user, duty_day):
        """Тест создания назначения через стандартный create"""
        url = reverse("dutyassignment-list")
        data = {"user": staff_user.id, "duty": duty_day.id}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DutyAssignment.objects.count() == 1

    def test_list_duty_assignments(self, api_client, duty_assignments):
        """Тест получения списка всех назначений"""
        url = reverse("dutyassignment-list")
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(duty_assignments)

    def test_delete_duty_assignment(self, api_client, duty_assignment):
        """Тест удаления назначения"""
        url = reverse("dutyassignment-detail", kwargs={"pk": duty_assignment.id})
        response = api_client.delete(url)

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DutyAssignment.objects.count() == 0


@pytest.mark.django_db
class TestDutyAssignmentViewSetEdgeCases:
    """Тесты граничных случаев для DutyAssignmentViewSet"""

    def test_generate_with_empty_dates(self, api_client):
        """Тест генерации с пустым списком дат"""
        url = reverse("dutyassignment-generate")
        data = {"dates": [], "people_per_day": 2}
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_with_days_off(self, api_client, staff_users, day_off, date_range):
        """Тест генерации расписания с учетом выходных дней"""
        url = reverse("dutyassignment-generate")
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        response = api_client.post(url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Проверяем, что пользователь с выходным не назначен на этот день
        assignments_on_day_off = DutyAssignment.objects.filter(
            user=day_off.user, duty__date=day_off.date
        )
        assert assignments_on_day_off.count() == 0
