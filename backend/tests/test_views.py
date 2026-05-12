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

    def test_list_staff_unauthenticated(self, api_client, staff_users):
        """Test listing all staff without authentication (AllowAny)"""
        response = api_client.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(staff_users)

    def test_list_staff_authenticated(self, authenticated_client, staff_users):
        """Test listing all staff with authentication"""
        response = authenticated_client.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(staff_users)

    def test_create_staff_unauthenticated(self, api_client):
        """Test creating staff without authentication - should fail"""
        data = {"first_name": "Test", "last_name": "User", "email": "test@example.com"}
        response = api_client.post("/api/users/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_staff_authenticated(self, authenticated_client):
        """Test creating new staff with authentication"""
        data = {"first_name": "Test", "last_name": "User", "email": "test@example.com"}
        response = authenticated_client.post("/api/users/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["first_name"] == "Test"
        assert response.data["full_name"] == "Test User"
        assert Staff.objects.count() == 1

    def test_retrieve_staff_unauthenticated(self, api_client, staff_user):
        """Test retrieving specific staff without authentication (AllowAny)"""
        response = api_client.get(f"/api/users/{staff_user.id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["id"] == staff_user.id
        assert response.data["email"] == staff_user.email

    def test_update_staff_unauthenticated(self, api_client, staff_user):
        """Test updating staff without authentication - should fail"""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }
        response = api_client.put(f"/api/users/{staff_user.id}/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_update_staff_authenticated(self, authenticated_client, staff_user):
        """Test updating staff with authentication"""
        data = {
            "first_name": "Updated",
            "last_name": "Name",
            "email": "updated@example.com",
        }
        response = authenticated_client.put(
            f"/api/users/{staff_user.id}/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["first_name"] == "Updated"

    def test_delete_staff_unauthenticated(self, api_client, staff_user):
        """Test deleting staff without authentication - should fail"""
        response = api_client.delete(f"/api/users/{staff_user.id}/")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_delete_staff_authenticated(self, authenticated_client, staff_user):
        """Test deleting staff with authentication"""
        response = authenticated_client.delete(f"/api/users/{staff_user.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert Staff.objects.count() == 0

    def test_create_staff_duplicate_email(self, authenticated_client, staff_user):
        """Test creating staff with duplicate email"""
        data = {"first_name": "Another", "last_name": "User", "email": staff_user.email}
        response = authenticated_client.post("/api/users/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stats_action_unauthenticated(self, api_client, staff_users):
        """Test stats action without authentication (AllowAny)"""
        from datetime import date

        # Create duties and assignments
        jan_duty = Duty.objects.create(date=date(2024, 1, 15))
        feb_duty = Duty.objects.create(date=date(2024, 2, 15))

        DutyAssignment.objects.create(user=staff_users[0], duty=jan_duty)
        DutyAssignment.objects.create(user=staff_users[0], duty=feb_duty)

        params = {"start_date": "2024-01-01", "end_date": "2024-02-28"}
        response = api_client.get("/api/users/stats/", params)

        assert response.status_code == status.HTTP_200_OK
        assert isinstance(response.data, list)

    def test_stats_action_missing_params(self, api_client):
        """Test stats action without required date parameters"""
        response = api_client.get("/api/users/stats/")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_stats_action_with_multiple_users(self, api_client, staff_users):
        """Test stats with multiple users having assignments"""
        from datetime import date

        # Create duties
        duty1 = Duty.objects.create(date=date(2024, 1, 10))
        duty2 = Duty.objects.create(date=date(2024, 1, 20))
        duty3 = Duty.objects.create(date=date(2024, 2, 10))

        # Assign to different users
        DutyAssignment.objects.create(user=staff_users[0], duty=duty1)
        DutyAssignment.objects.create(user=staff_users[0], duty=duty2)
        DutyAssignment.objects.create(user=staff_users[1], duty=duty3)

        params = {"start_date": "2024-01-01", "end_date": "2024-02-28"}
        response = api_client.get("/api/users/stats/", params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= 2  # At least 2 users with assignments


@pytest.mark.django_db
class TestDaysOffViewSet:
    """Tests for DaysOffViewSet"""

    def test_list_days_off_unauthenticated(
        self, api_client, days_off_multiple, date_range
    ):
        """Test listing days off without authentication (AllowAny)"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        response = api_client.get("/api/days-off/", params)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(days_off_multiple)

    def test_create_day_off_unauthenticated(self, api_client, staff_user, tomorrow):
        """Test creating day off without authentication - should fail"""
        data = {"user": staff_user.id, "date": tomorrow.isoformat()}
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_day_off_authenticated(
        self, authenticated_client, staff_user, tomorrow
    ):
        """Test creating day off with authentication"""
        data = {"user": staff_user.id, "dates": [tomorrow.isoformat()]}
        response = authenticated_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DaysOff.objects.count() == 1

    def test_create_day_off_past_date(
        self, authenticated_client, staff_user, yesterday
    ):
        """Test creating day off with past date - should fail"""
        data = {"user": staff_user.id, "dates": [yesterday.isoformat()]}
        response = authenticated_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Нельзя добавить дату из прошлого" in str(response.data)

    def test_create_duplicate_day_off(self, authenticated_client, day_off):
        """Test creating duplicate day off"""
        data = {"user": day_off.user.id, "dates": [day_off.date.isoformat()]}
        response = authenticated_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "уже есть выходные" in str(response.data)

    def test_delete_day_off_unauthenticated(self, api_client, day_off):
        """Test deleting day off without authentication - should fail"""
        response = api_client.delete(f"/api/days-off/{day_off.id}/")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_delete_day_off_authenticated(self, authenticated_client, day_off):
        """Test deleting day off with authentication"""
        response = authenticated_client.delete(f"/api/days-off/{day_off.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DaysOff.objects.count() == 0

    def test_bulk_create_days_off_authenticated(
        self, authenticated_client, staff_user, date_range
    ):
        """Test creating multiple days off at once with authentication"""
        dates = date_range["dates"][:3]
        data = {"user": staff_user.id, "dates": [d.isoformat() for d in dates]}
        response = authenticated_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert isinstance(response.data, list)
        assert len(response.data) == 3
        assert DaysOff.objects.filter(user=staff_user).count() == 3

    def test_bulk_create_days_off_unauthenticated(
        self, api_client, staff_user, date_range
    ):
        """Test bulk creating days off without authentication - should fail"""
        dates = date_range["dates"][:3]
        data = {"user": staff_user.id, "dates": [d.isoformat() for d in dates]}
        response = api_client.post("/api/days-off/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_bulk_create_days_off_single_date(
        self, authenticated_client, staff_user, tomorrow
    ):
        """Test bulk create with single date"""
        data = {"user": staff_user.id, "dates": [tomorrow.isoformat()]}
        response = authenticated_client.post("/api/days-off/", data, format="json")
        logger.info(response)
        assert response.status_code == status.HTTP_201_CREATED
        assert len(response.data) == 1
        assert DaysOff.objects.count() == 1

    def test_bulk_create_days_off_past_date(
        self, authenticated_client, staff_user, yesterday, tomorrow
    ):
        """Test bulk create with past date should fail"""
        data = {
            "user": staff_user.id,
            "dates": [yesterday.isoformat(), tomorrow.isoformat()],
        }
        response = authenticated_client.post("/api/days-off/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_days_off_without_filter(self, api_client, days_off_multiple):
        """Test listing days off without date filter"""
        response = api_client.get("/api/days-off/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) >= len(days_off_multiple)


@pytest.mark.django_db
class TestDutyAssignmentViewSet:
    """Tests for DutyAssignmentViewSet"""

    def test_list_assignments_unauthenticated(
        self, api_client, duty_assignments, date_range
    ):
        """Test list_assignments action without authentication (AllowAny)"""
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

    def test_generate_duty_plan_unauthenticated(
        self, api_client, staff_users, date_range
    ):
        """Test generating duty schedule without authentication - should fail"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        response = api_client.post("/api/duties/generate/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_generate_duty_plan_authenticated(
        self, authenticated_client, staff_users, date_range
    ):
        """Test generating duty schedule with authentication"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 2,
        }
        response = authenticated_client.post(
            "/api/duties/generate/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data
        assert "errors" in response.data

        # Check duties were created
        assert Duty.objects.count() == len(date_range["dates"])

    def test_generate_with_insufficient_staff(
        self, authenticated_client, staff_user, date_range
    ):
        """Test generation with insufficient staff"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 5,
        }
        response = authenticated_client.post(
            "/api/duties/generate/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data.get("errors", {})) > 0

    def test_generate_invalid_people_per_day(self, authenticated_client, date_range):
        """Test generation with invalid people_per_day"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"]],
            "people_per_day": 15,  # Max is 10
        }
        response = authenticated_client.post(
            "/api/duties/generate/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_generate_empty_dates(self, authenticated_client):
        """Test generation with empty dates list"""
        data = {"dates": [], "people_per_day": 2}
        response = authenticated_client.post(
            "/api/duties/generate/", data, format="json"
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_assign_new_user_unauthenticated(
        self, api_client, staff_user, duty_day, date_range
    ):
        """Test assigning new user without authentication - should fail"""
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
            "/api/duties/assign/", data, params=params, format="json"
        )

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_assign_new_user_authenticated(
        self, authenticated_client, staff_user, duty_day, date_range
    ):
        """Test assigning new user to duty with authentication"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = authenticated_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert "data" in response.data

        # Check assignment was created
        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

    def test_change_assignment_authenticated(
        self, authenticated_client, duty_assignment, staff_users, date_range
    ):
        """Test changing assignment (replace user) with authentication"""
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
        response = authenticated_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Check assignment was updated
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

    def test_remove_assignment_authenticated(
        self, authenticated_client, duty_assignment, date_range
    ):
        """Test removing assignment with authentication"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": duty_assignment.user.id,
            "user_id_new": None,
            "date": duty_assignment.duty.date.isoformat(),
        }
        response = authenticated_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )

        assert response.status_code == status.HTTP_200_OK

        # Check assignment was deleted
        assert not DutyAssignment.objects.filter(id=duty_assignment.id).exists()

    def test_assign_missing_query_params(
        self, authenticated_client, staff_user, duty_day
    ):
        """Test assign without required query params"""
        data = {
            "user_id_prev": None,
            "user_id_new": staff_user.id,
            "date": duty_day.date.isoformat(),
        }
        response = authenticated_client.post("/api/duties/assign/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_duty_assignments(self, api_client, duty_assignments):
        """Test listing all duty assignments"""
        response = api_client.get("/api/duties/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(duty_assignments)

    def test_create_duty_assignment(self, authenticated_client, staff_user, duty_day):
        """Test creating duty assignment via standard create"""
        data = {"user": staff_user.id, "duty": duty_day.id}
        response = authenticated_client.post("/api/duties/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert DutyAssignment.objects.count() == 1

    def test_delete_duty_assignment(self, authenticated_client, duty_assignment):
        """Test deleting duty assignment"""
        response = authenticated_client.delete(f"/api/duties/{duty_assignment.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert DutyAssignment.objects.count() == 0


@pytest.mark.django_db
class TestViewSetIntegration:
    """Integration tests for ViewSets"""

    def test_full_workflow(self, authenticated_client, staff_users, date_range):
        """Test complete workflow: create duties -> generate -> modify"""
        # 1. Generate schedule
        data = {
            "dates": [d.isoformat() for d in date_range["dates"][:3]],
            "people_per_day": 2,
        }
        response = authenticated_client.post(
            "/api/duties/generate/", data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        # 2. List assignments
        params = {
            "start_date": date_range["dates"][0].isoformat(),
            "end_date": date_range["dates"][2].isoformat(),
        }
        response = authenticated_client.get("/api/duties/list_assignments/", params)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 3

        # 3. Modify assignment
        first_duty = Duty.objects.filter(date=date_range["dates"][0]).first()
        first_assignment = DutyAssignment.objects.filter(duty=first_duty).first()

        if first_assignment:
            modify_data = {
                "user_id_prev": first_assignment.user.id,
                "user_id_new": staff_users[-1].id,
                "date": first_duty.date.isoformat(),
            }
            response = authenticated_client.post(
                "/api/duties/assign/", modify_data, query_params=params, format="json"
            )
            assert response.status_code == status.HTTP_200_OK
