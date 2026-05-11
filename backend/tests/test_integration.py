"""
Integration tests between accounts and planner apps
"""

import pytest
from datetime import date
from rest_framework import status
from accounts.models import User, Invitation
from planner.models import Staff, DaysOff, Duty, DutyAssignment


@pytest.mark.django_db
class TestUserToStaffIntegration:
    """Tests for integration between User auth and Staff management"""

    def test_authenticated_user_can_create_staff(self, authenticated_client):
        """Test that authenticated user can create staff members"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
        }

        response = authenticated_client.post("/api/users/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert Staff.objects.filter(email="john.doe@example.com").exists()

    def test_unauthenticated_user_cannot_create_staff(self, api_client):
        """Test that unauthenticated user cannot create staff"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
        }

        response = api_client.post("/api/users/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]
        assert not Staff.objects.filter(email="john.doe@example.com").exists()

    def test_user_can_view_staff_without_auth(self, api_client, staff_users):
        """Test that anyone can view staff list (AllowAny)"""
        response = api_client.get("/api/users/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == len(staff_users)


@pytest.mark.django_db
class TestInvitationWorkflow:
    """Tests for complete invitation workflow"""

    def test_admin_creates_invitation_new_user_registers(
        self, authenticated_client, api_client
    ):
        """Test full invitation workflow: create -> register -> login"""
        # 1. Admin creates invitation
        import os

        os.environ["FRONTEND_URL"] = "http://localhost:3000"

        response = authenticated_client.post("/api/auth/invite/")

        assert response.status_code == status.HTTP_201_CREATED
        assert "url" in response.data

        # Extract token from URL
        token = response.data["url"].split("token=")[1]

        # 2. New user registers with the invitation token
        register_data = {
            "email": "newuser@example.com",
            "password1": "newpass123",
            "password2": "newpass123",
            "token": token,  # Use the token from invitation
        }

        register_response = api_client.post(
            "/api/auth/registration/", register_data, format="json"
        )

        assert register_response.status_code == status.HTTP_201_CREATED

        # 3. New user can login
        login_data = {"email": "newuser@example.com", "password": "newpass123"}

        login_response = api_client.post("/api/auth/login/", login_data, format="json")

        assert login_response.status_code == status.HTTP_200_OK

    def test_invitation_token_is_valid_initially(self, authenticated_client):
        """Test that newly created invitation is valid"""
        response = authenticated_client.post("/api/auth/invite/")

        assert response.status_code == status.HTTP_201_CREATED

        # Get the created invitation
        invitation = Invitation.objects.last()
        assert invitation.is_valid() is True


@pytest.mark.django_db
class TestAuthenticatedDutyManagement:
    """Tests for duty management requiring authentication"""

    def test_create_duty_schedule_requires_auth(
        self, api_client, staff_users, date_range
    ):
        """Test that generating duty schedule requires authentication"""
        data = {
            "dates": [d.isoformat() for d in date_range["dates"][:3]],
            "people_per_day": 2,
        }

        # Unauthenticated - should fail
        response = api_client.post("/api/duties/generate/", data, format="json")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_modify_assignment_requires_auth(
        self, api_client, staff_users, duty_day, date_range
    ):
        """Test that modifying assignments requires authentication"""
        params = {
            "start_date": date_range["start"].isoformat(),
            "end_date": date_range["end"].isoformat(),
        }
        data = {
            "user_id_prev": None,
            "user_id_new": staff_users[0].id,
            "date": duty_day.date.isoformat(),
        }

        # Unauthenticated - should fail
        response = api_client.post(
            "/api/duties/assign/", data, query_params=params, format="json"
        )
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_create_days_off_requires_auth(self, api_client, staff_user, tomorrow):
        """Test that creating days off requires authentication"""
        data = {"user": staff_user.id, "dates": [tomorrow.isoformat()]}

        # Unauthenticated - should fail
        response = api_client.post("/api/days-off/", data, format="json")
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


@pytest.mark.django_db
class TestCompleteWorkflow:
    """End-to-end workflow tests"""

    def test_complete_duty_planning_workflow(
        self, authenticated_client, api_client, admin_user
    ):
        """Test complete workflow: register -> create staff -> schedule duties"""
        from accounts.models import Invitation

        # 0. Create invitation for new user
        invitation = Invitation.objects.create(created_by=admin_user)

        # 1. Register (this gives us authenticated session)
        register_data = {
            "email": "newadmin@example.com",
            "password1": "adminpass123",
            "password2": "adminpass123",
            "token": str(invitation.token),
        }

        api_client.post("/api/auth/registration/", register_data, format="json")

        # 2. Login to get fresh auth
        login_data = {"email": "newadmin@example.com", "password": "adminpass123"}

        api_client.post("/api/auth/login/", login_data, format="json")

        # 3. Create staff members
        staff_data_list = [
            {"first_name": "Alice", "last_name": "Smith", "email": "alice@example.com"},
            {"first_name": "Bob", "last_name": "Jones", "email": "bob@example.com"},
            {"first_name": "Carol", "last_name": "White", "email": "carol@example.com"},
        ]

        for staff_data in staff_data_list:
            response = api_client.post("/api/users/", staff_data, format="json")
            assert response.status_code == status.HTTP_201_CREATED

        assert Staff.objects.count() == 3

        # 4. Create duty days and generate schedule
        from django.utils import timezone
        from datetime import timedelta

        today = timezone.localdate()
        dates = [today + timedelta(days=i) for i in range(1, 8)]

        schedule_data = {"dates": [d.isoformat() for d in dates], "people_per_day": 2}

        response = api_client.post(
            "/api/duties/generate/", schedule_data, format="json"
        )
        assert response.status_code == status.HTTP_200_OK

        # 5. Verify duties were created
        assert Duty.objects.count() == 7

        # 6. Verify assignments were created
        assert DutyAssignment.objects.count() > 0

        # 7. View the schedule (no auth required for viewing)
        unauthenticated_client = api_client.__class__()  # Fresh client without auth

        list_params = {
            "start_date": dates[0].isoformat(),
            "end_date": dates[-1].isoformat(),
        }

        response = unauthenticated_client.get(
            "/api/duties/list_assignments/", list_params
        )
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["data"]) == 7

    def test_invited_user_can_manage_duties(self, authenticated_client, api_client):
        """Test that user registered via invitation can manage duties"""
        # 1. Admin creates invitation
        import os

        os.environ["FRONTEND_URL"] = "http://localhost:3000"

        inv_response = authenticated_client.post("/api/auth/invite/")
        assert inv_response.status_code == status.HTTP_201_CREATED

        # Extract token from invitation URL
        token = inv_response.data["url"].split("token=")[1]

        # 2. New user registers with the token
        register_data = {
            "email": "invited@example.com",
            "password1": "invitedpass123",
            "password2": "invitedpass123",
            "token": token,  # Use the invitation token
        }

        api_client.post("/api/auth/registration/", register_data, format="json")

        # 3. Login
        login_data = {"email": "invited@example.com", "password": "invitedpass123"}

        api_client.post("/api/auth/login/", login_data, format="json")

        # 4. Create staff
        staff_data = {
            "first_name": "Test",
            "last_name": "Staff",
            "email": "test.staff@example.com",
        }

        response = api_client.post("/api/users/", staff_data, format="json")
        assert response.status_code == status.HTTP_201_CREATED

        # 5. User can now manage their staff
        assert Staff.objects.filter(email="test.staff@example.com").exists()


@pytest.mark.django_db
class TestPermissionBoundaries:
    """Tests for permission boundaries between models"""

    def test_staff_and_user_are_separate_models(self):
        """Test that Staff and User are distinct models"""
        # Create User
        user = User.objects.create_user(email="user@example.com", password="pass123")

        # Create Staff
        staff = Staff.objects.create(
            first_name="Staff", last_name="Member", email="staff@example.com"
        )

        # They are different models
        assert User.objects.count() == 1
        assert Staff.objects.count() == 1
        assert user.email != staff.email

    def test_staff_email_can_differ_from_user_email(self):
        """Test that Staff email is independent of User email"""
        # User for authentication
        User.objects.create_user(email="admin@example.com", password="pass123")

        # Staff member (could have different email)
        Staff.objects.create(
            first_name="Employee", last_name="One", email="employee@example.com"
        )

        assert User.objects.filter(email="admin@example.com").exists()
        assert Staff.objects.filter(email="employee@example.com").exists()
        assert not User.objects.filter(email="employee@example.com").exists()
