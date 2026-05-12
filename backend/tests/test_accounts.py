"""
Tests for accounts app (User authentication and registration)
"""

import pytest
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, Invitation
from rest_framework import status


@pytest.mark.django_db
class TestUserModel:
    """Tests for custom User model"""

    def test_create_user_with_email(self):
        """Test creating user with email as username field"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        assert user.email == "test@example.com"
        assert user.username  # Should be auto-generated UUID
        assert user.check_password("testpass123")
        assert not user.is_staff
        assert not user.is_superuser

    def test_create_user_without_email(self):
        """Test that creating user without email raises error"""
        with pytest.raises(ValueError, match="Please write an email"):
            User.objects.create_user(email="", password="testpass123")

    def test_create_superuser(self):
        """Test creating superuser"""
        user = User.objects.create_superuser(
            email="admin@example.com", password="adminpass123"
        )

        assert user.email == "admin@example.com"
        assert user.is_staff
        assert user.is_superuser

    def test_user_str_representation(self):
        """Test User string representation"""
        user = User.objects.create_user(
            email="test@example.com", password="testpass123"
        )

        assert str(user) == "test@example.com"

    def test_email_normalization(self):
        """Test that email is normalized"""
        user = User.objects.create_user(
            email="Test@EXAMPLE.com", password="testpass123"
        )

        assert user.email == "Test@example.com"  # Domain lowercase

    def test_unique_email_constraint(self):
        """Test that email must be unique"""
        User.objects.create_user(email="test@example.com", password="testpass123")

        with pytest.raises(Exception):  # IntegrityError
            User.objects.create_user(email="test@example.com", password="anotherpass")


@pytest.mark.django_db
class TestInvitationModel:
    """Tests for Invitation model"""

    @pytest.fixture
    def admin_user(self):
        """Create an admin user for creating invitations"""
        return User.objects.create_user(
            email="admin@example.com", password="adminpass123"
        )

    def test_create_invitation(self, admin_user):
        """Test creating invitation"""
        invitation = Invitation.objects.create(created_by=admin_user)

        assert invitation.token
        assert invitation.created_by == admin_user
        assert invitation.created_at

    def test_invitation_token_is_unique(self, admin_user):
        """Test that invitation tokens are unique UUIDs"""
        inv1 = Invitation.objects.create(created_by=admin_user)
        inv2 = Invitation.objects.create(created_by=admin_user)

        assert inv1.token != inv2.token

    def test_invitation_is_valid_within_hour(self, admin_user):
        """Test that invitation is valid within 1 hour"""
        invitation = Invitation.objects.create(created_by=admin_user)

        assert invitation.is_valid() is True

    def test_invitation_expires_after_hour(self, admin_user):
        """Test that invitation expires after 1 hour"""
        invitation = Invitation.objects.create(created_by=admin_user)

        # Manually set created_at to 2 hours ago
        invitation.created_at = timezone.now() - timedelta(hours=2)
        invitation.save()

        assert invitation.is_valid() is False

    def test_invitation_str_representation(self, admin_user):
        """Test Invitation string representation"""
        invitation = Invitation.objects.create(created_by=admin_user)

        str_repr = str(invitation)
        assert "admin@example.com" in str_repr
        assert "Invitation by" in str_repr

    def test_cascade_delete_on_user_deletion(self, admin_user):
        """Test that invitations are deleted when user is deleted"""
        Invitation.objects.create(created_by=admin_user)
        Invitation.objects.create(created_by=admin_user)

        # Store user_id before deletion
        user_id = admin_user.id

        assert Invitation.objects.filter(created_by_id=user_id).count() == 2

        admin_user.delete()

        # After deletion, no invitations should exist for this user_id
        assert Invitation.objects.filter(created_by_id=user_id).count() == 0


@pytest.mark.django_db
class TestCreateInvitationView:
    """Tests for CreateInvitationView"""

    @pytest.fixture
    def admin_user(self):
        return User.objects.create_user(
            email="admin@example.com", password="adminpass123"
        )

    @pytest.fixture
    def authenticated_client(self, api_client, admin_user):
        """API client with authenticated user"""
        api_client.force_authenticate(user=admin_user)
        return api_client

    def test_create_invitation_authenticated(self, authenticated_client):
        """Test creating invitation as authenticated user"""
        response = authenticated_client.post("/api/auth/invite/")

        assert response.status_code == status.HTTP_201_CREATED
        assert "url" in response.data
        assert "token=" in response.data["url"]
        assert Invitation.objects.count() == 1

    def test_create_invitation_unauthenticated(self, api_client):
        """Test that unauthenticated user cannot create invitation"""
        response = api_client.post("/api/auth/invite/")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_invitation_url_format(self, authenticated_client, settings):
        """Test that invitation URL has correct format"""
        # Set FRONTEND_URL for test
        import os

        os.environ["FRONTEND_URL"] = "http://localhost:3000"

        response = authenticated_client.post("/api/auth/invite/")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["url"].startswith("http://localhost:3000/register?token=")


@pytest.mark.django_db
class TestRegisterView:
    """Tests for RegisterView"""

    @pytest.fixture
    def valid_invitation(self, admin_user):
        """Create a valid invitation for registration tests"""
        return Invitation.objects.create(created_by=admin_user)

    def test_register_new_user(self, api_client, valid_invitation):
        """Test registering new user with valid invitation token"""
        data = {
            "email": "newuser@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(valid_invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert "user" in response.data
        assert response.data["user"]["email"] == "newuser@example.com"

        # Check user was created
        assert User.objects.filter(email="newuser@example.com").exists()

        # Check JWT cookies are set
        assert len(response.cookies) > 0 or "Set-Cookie" in response

    def test_register_duplicate_email(self, api_client, valid_invitation):
        """Test registering with existing email"""
        # Create existing user
        User.objects.create_user(email="existing@example.com", password="pass123")

        data = {
            "email": "existing@example.com",
            "password1": "newpass123",
            "password2": "newpass123",
            "token": str(valid_invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in response.data
        assert "already exists" in str(response.data["email"][0]).lower()

    def test_register_invalid_data(self, api_client, valid_invitation):
        """Test registration with invalid data"""
        data = {
            "email": "invalid-email",  # Invalid email format
            "password1": "pass",
            "password2": "different",  # Passwords don't match
            "token": str(valid_invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_sets_jwt_cookies(self, api_client, valid_invitation):
        """Test that registration sets JWT cookies"""
        data = {
            "email": "cookieuser@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(valid_invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_201_CREATED

        # Check response has Set-Cookie header or cookies set
        # Note: exact implementation depends on your set_jwt_cookies function
        assert len(response.cookies) > 0 or "Set-Cookie" in response

    def test_register_password_validation(self, api_client, valid_invitation):
        """Test registration with weak password"""
        data = {
            "email": "test@example.com",
            "password1": "123",  # Too short
            "password2": "123",
            "token": str(valid_invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_without_token(self, api_client):
        """Test registration without invitation token - should fail"""
        data = {
            "email": "notoken@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            # Missing token
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "token" in response.data or "non_field_errors" in response.data

    def test_register_with_invalid_token(self, api_client):
        """Test registration with invalid token"""
        import uuid

        data = {
            "email": "invalidtoken@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(uuid.uuid4()),  # Random UUID that doesn't exist
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_register_with_expired_token(self, api_client, admin_user):
        """Test registration with expired invitation token"""
        from datetime import timedelta
        from django.utils import timezone

        # Create expired invitation (2 hours old)
        invitation = Invitation.objects.create(created_by=admin_user)
        invitation.created_at = timezone.now() - timedelta(hours=2)
        invitation.save()

        data = {
            "email": "expired@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(invitation.token),
        }

        response = api_client.post("/api/auth/registration/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Should contain error about expired invitation
        assert "expired" in str(response.data).lower() or "token" in response.data


@pytest.mark.django_db
class TestAuthenticationIntegration:
    """Integration tests for authentication flow"""

    def test_full_registration_and_login_flow(self, api_client, admin_user):
        """Test complete registration and authentication flow"""
        # 0. Create valid invitation
        invitation = Invitation.objects.create(created_by=admin_user)

        # 1. Register new user
        register_data = {
            "email": "flowtest@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(invitation.token),
        }

        register_response = api_client.post(
            "/api/auth/registration/", register_data, format="json"
        )

        assert register_response.status_code == status.HTTP_201_CREATED

        # 2. User should be created
        user = User.objects.get(email="flowtest@example.com")
        assert user is not None
        assert user.check_password("strongpass123")

        # 3. User should receive JWT tokens (cookies)
        assert len(register_response.cookies) > 0 or "Set-Cookie" in register_response
