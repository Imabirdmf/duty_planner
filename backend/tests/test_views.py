"""
Tests for ViewSets (API endpoints)
"""

import datetime

import pytest
from rest_framework import status
from planner.models import Staff, DaysOff, Duty, DutyAssignment
import logging

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestStaffViewSet:
    """Tests for StaffViewSet"""

    def test_list_staff(self, api_client, staff_users):
        """Test listing all staff"""
        response = api_client.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(staff_users)

    def test_create_staff(self, api_client):
        """Test creating new staff"""
        data = {"first_name": "Test", "last_name": "User", "email": "test@example.com"}
        response = api_client.post("/api/users/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Test"
        assert response.data["full_name"] == "Test User"
        assert Staff.objects.count() == 1

    def test_retrieve_staff(self, api_client, staff_user):
        """Test retrieving specific staff"""
        response = api_client.get(f"/api/users/{staff_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == staff_user.id
        assert response.data["email"] == staff_user.email

    def test_update_staff(self, api_client, staff_user):
        """Test updating staff"""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }
        response = api_client.put(f"/api/users/{staff_user.id}/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_delete_staff(self, api_client, staff_user):
        """Test deleting staff"""
        response = api_client.delete(f"/api/users/{staff_user.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Staff.objects.count() == 0

    def test_create_staff_duplicate_email(self, api_client, staff_user):
        """Test creating staff with duplicate email"""
        data = {"first_name": "Another", "last_name": "User", "email": staff_user.email}
        response = api_client.post("/api/users/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestDaysOffViewSet:
    """Tests for DaysOffViewSet"""

    def test_list_days_off(self, api_client, days_off_multiple, date_range):
        """Test listing days off with date filter"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        response = api_client.get("/api/days-off/", params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(days_off_multiple)

    def test_create_day_off(self, api_client, staff_user, tomorrow):
        """Test creating day off"""
        data = {"user": staff_user.id, "dates": [tomorrow.isoformat()]}
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DaysOff.objects.count() == 1

    def test_create_days_off(self, api_client, staff_user, tomorrow):
        """Test creating day off"""
        data = {
            "user": staff_user.id,
            "dates": [
                tomorrow.isoformat(),
                (tomorrow + datetime.timedelta(days=1)).isoformat(),
            ],
        }
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DaysOff.objects.count() == 2

    def test_create_day_off_past_date(self, api_client, staff_user, yesterday):
        """Test creating day off with past date - should fail"""
        data = {"user": staff_user.id, "dates": [yesterday.isoformat()]}
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Нельзя добавить дату из прошлого" in str(response.data)

    def test_create_duplicate_day_off(self, api_client, day_off):
        """Test creating duplicate day off"""
        data = {"user": day_off.user.id, "dates": [day_off.date.isoformat()]}
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "уже есть выходные" in str(response.data)

    def test_delete_day_off(self, api_client, day_off):
        """Test deleting day off"""
        logger.info("day-off: %s", day_off.id)
        response = api_client.delete(f"/api/days-off/{day_off.id}/")
        logger.info("response: %s", response)
        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DaysOff.objects.count() == 0


@pytest.mark.django_db
class TestDutyAssignmentViewSet:
    """Tests for DutyAssignmentViewSet"""

    def test_list_assignments(self, api_client, duty_assignments, date_range):
        """Test list_assignments action"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        response = api_client.get("/api/duties/list_assignments/", params)

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert len(response.data["data"]) > 0

    def test_list_assignments_missing_params(self, api_client):
        """Test list_assignments without required params"""
        response = api_client.get("/api/duties/list_assignments/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_duty_plan(self, api_client, staff_users, date_range):
        """Test generating duty schedule"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        response = api_client.post("/api/duties/generate/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "errors" in response.data

        # Check duties were created
        assert Duty.objects.count() == len(date_range["dates"])

    def test_generate_with_insufficient_staff(self, api_client, staff_user, date_range):
        """Test generation with insufficient staff"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 5,
        }
        response = api_client.post("/api/duties/generate/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get("errors", {})) > 0

    def test_generate_invalid_people_per_day(self, api_client, date_range):
        """Test generation with invalid people_per_day"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 15,  # Max is 10
        }
        response = api_client.post("/api/duties/generate/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_empty_dates(self, api_client):
        """Test generation with empty dates list"""
        data = {"dates": [], "people_per_day": 2}
        response = api_client.post("/api/duties/generate/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_new_user(self, api_client, staff_user, duty_day, date_range):
        """Test assigning new user to duty"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = api_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )
        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data

        # Check assignment was created
        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

    def test_change_assignment(
        self, api_client, duty_assignment, staff_users, date_range
    ):
        """Test changing assignment (replace user)"""
        new_user = staff_users[1]
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": duty_assignment.user.id,
            "user_id_new": new_user.id,
            "date": duty_assignment.duty.date.isoformat(),
        }
        response = api_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Check assignment was updated
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

    def test_remove_assignment(self, api_client, duty_assignment, date_range):
        """Test removing assignment"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": duty_assignment.user.id,
            "user_id_new": None,
            "date": duty_assignment.duty.date.isoformat(),
        }
        response = api_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Check assignment was deleted
        assert not DutyAssignment.objects.filter(id=duty_assignment.id).exists()

    def test_assign_missing_query_params(self, api_client, staff_user, duty_day):
        """Test assign without required query params"""
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = api_client.post("/api/duties/assign/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_duty_assignments(self, api_client, duty_assignments):
        """Test listing all duty assignments"""
        response = api_client.get("/api/duties/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(duty_assignments)

    def test_create_duty_assignment(self, api_client, staff_user, duty_day):
        """Test creating duty assignment via standard create"""
        data = {"user": staff_user.id, "duty": duty_day.id}
        response = api_client.post("/api/duties/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DutyAssignment.objects.count() == 1

    def test_delete_duty_assignment(self, api_client, duty_assignment):
        """Test deleting duty assignment"""
        response = api_client.delete(f"/api/duties/{duty_assignment.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DutyAssignment.objects.count() == 0


@pytest.mark.django_db
class TestViewSetIntegration:
    """Integration tests for ViewSets"""

    def test_full_workflow(self, api_client, staff_users, date_range):
        """Test complete workflow: create duties -> generate -> modify"""
        # 1. Generate schedule
        data = {
            "dates": [d.isoformat() for d in date_range["dates"][:3]],
            "people_per_day": 2,
        }
        response = api_client.post("/api/duties/generate/", data, format="json")
        assert response.status_code == status.HTTP_200_OK
        print("# 1. Generate schedule")

        # 2. List assignments
        params = {
            "start_date": date_range["dates"][0].isoformat(),
            "end_date": date_range["dates"][2].isoformat(),
        }
        response = api_client.get("/api/duties/list_assignments/", query_params=params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3
        print("# 2. List assignments")

        # 3. Modify assignment
        first_duty = Duty.objects.filter(date=date_range["dates"][0]).first()
        first_assignment = DutyAssignment.objects.filter(duty=first_duty).first()

        if first_assignment:
            modify_data = {
                "user_id_prev": first_assignment.user.id,
                "user_id_new": staff_users[-1].id,
                "date": first_duty.date.isoformat(),
            }
            response = api_client.post(
                "/api/duties/assign/", modify_data, query_params=params, format="json"
            )
            assert response.status_code == status.HTTP_200_OK
        print("# 3. Modify assignment")
