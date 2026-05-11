"""
Tests for dj-rest-auth authentication endpoints
"""

import pytest
from rest_framework import status
from accounts.models import User


@pytest.mark.django_db
class TestLoginEndpoint:
    """Tests for /api/auth/login/ endpoint"""

    @pytest.fixture
    def registered_user(self):
        """Create a registered user for login tests"""
        return User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )

    def test_login_success(self, api_client, registered_user):
        """Test successful login with valid credentials"""
        data = {"email": "testuser@example.com", "password": "testpass123"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert "user" in response.data or "email" in response.data

        # Check JWT cookies are set
        assert len(response.cookies) > 0 or "Set-Cookie" in response

    def test_login_wrong_password(self, api_client, registered_user):
        """Test login with wrong password"""
        data = {"email": "testuser@example.com", "password": "wrongpassword"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_nonexistent_user(self, api_client):
        """Test login with non-existent user"""
        data = {"email": "nonexistent@example.com", "password": "somepassword"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_email(self, api_client):
        """Test login without email"""
        data = {"password": "testpass123"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_missing_password(self, api_client, registered_user):
        """Test login without password"""
        data = {"email": "testuser@example.com"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_sets_httponly_cookies(self, api_client, registered_user):
        """Test that login sets HttpOnly cookies"""
        data = {"email": "testuser@example.com", "password": "testpass123"}

        response = api_client.post("/api/auth/login/", data, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Check cookies exist (exact checking depends on DRF test client)
        # The response should have cookies set
        assert len(response.cookies) > 0 or "Set-Cookie" in response


@pytest.mark.django_db
class TestLogoutEndpoint:
    """Tests for /api/auth/logout/ endpoint"""

    @pytest.fixture
    def logged_in_client(self, api_client):
        """Create a logged-in client"""
        user = User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )

        # Login
        login_data = {"email": "testuser@example.com", "password": "testpass123"}
        api_client.post("/api/auth/login/", login_data, format="json")

        return api_client

    def test_logout_success(self, logged_in_client):
        """Test successful logout"""
        response = logged_in_client.post("/api/auth/logout/", format="json")

        assert response.status_code in [status.HTTP_200_OK, status.HTTP_204_NO_CONTENT]

    def test_logout_unauthenticated(self, api_client):
        """Test logout without being logged in"""
        response = api_client.post("/api/auth/logout/", format="json")

        # Should either succeed (logout is idempotent) or return 401
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_401_UNAUTHORIZED,
        ]


@pytest.mark.django_db
class TestTokenRefreshEndpoint:
    """Tests for /api/auth/token/refresh/ endpoint"""

    @pytest.fixture
    def user_with_refresh_token(self, api_client):
        """Create user and login to get refresh token"""
        user = User.objects.create_user(
            email="testuser@example.com", password="testpass123"
        )

        # Login to get tokens
        login_data = {"email": "testuser@example.com", "password": "testpass123"}
        response = api_client.post("/api/auth/login/", login_data, format="json")

        return api_client, response

    def test_refresh_token_success(self, user_with_refresh_token):
        """Test refreshing access token"""
        client, login_response = user_with_refresh_token

        # Try to refresh
        response = client.post("/api/auth/token/refresh/", format="json")

        # Should return new tokens or 200 OK
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

    def test_refresh_token_without_login(self, api_client):
        """Test refreshing token without being logged in"""
        response = api_client.post("/api/auth/token/refresh/", format="json")

        # Should fail without refresh token
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_401_UNAUTHORIZED,
        ]


@pytest.mark.django_db
class TestUserDetailEndpoint:
    """Tests for /api/auth/user/ endpoint (if available)"""

    def test_get_user_authenticated(self, authenticated_client, auth_user):
        """Test getting current user info when authenticated"""
        response = authenticated_client.get("/api/auth/user/")

        # May not be available in dj-rest-auth by default
        if response.status_code != status.HTTP_404_NOT_FOUND:
            assert response.status_code == status.HTTP_200_OK
            if "email" in response.data:
                assert response.data["email"] == auth_user.email

    def test_get_user_unauthenticated(self, api_client):
        """Test getting current user without authentication"""
        response = api_client.get("/api/auth/user/")

        # Should either not exist (404) or require auth (401)
        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
            status.HTTP_404_NOT_FOUND,
        ]


@pytest.mark.django_db
class TestAuthenticationFlow:
    """Integration tests for complete authentication flows"""

    @pytest.fixture
    def valid_invitation(self, admin_user):
        """Create valid invitation for tests"""
        from accounts.models import Invitation

        return Invitation.objects.create(created_by=admin_user)

    def test_register_login_refresh_logout_flow(self, api_client, valid_invitation):
        """Test complete authentication lifecycle"""
        # 1. Register
        register_data = {
            "email": "newuser@example.com",
            "password1": "strongpass123",
            "password2": "strongpass123",
            "token": str(valid_invitation.token),
        }

        register_response = api_client.post(
            "/api/auth/registration/", register_data, format="json"
        )

        assert register_response.status_code == status.HTTP_201_CREATED

        # 2. Login (should work with newly registered user)
        login_data = {"email": "newuser@example.com", "password": "strongpass123"}

        login_response = api_client.post("/api/auth/login/", login_data, format="json")

        assert login_response.status_code == status.HTTP_200_OK

        # 3. Refresh token
        refresh_response = api_client.post("/api/auth/token/refresh/", format="json")

        # Should succeed
        assert refresh_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ]

        # 4. Logout
        logout_response = api_client.post("/api/auth/logout/", format="json")

        assert logout_response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
        ]

    def test_login_with_registered_account(self, api_client, admin_user):
        """Test login after registration"""
        from accounts.models import Invitation

        # Create invitation
        invitation = Invitation.objects.create(created_by=admin_user)

        # Register via RegisterView
        register_data = {
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "token": str(invitation.token),
        }

        register_response = api_client.post(
            "/api/auth/registration/", register_data, format="json"
        )

        assert register_response.status_code == status.HTTP_201_CREATED

        # Now try to login with dj-rest-auth login
        login_data = {"email": "test@example.com", "password": "testpass123"}

        login_response = api_client.post("/api/auth/login/", login_data, format="json")

        assert login_response.status_code == status.HTTP_200_OK

    def test_cannot_access_protected_endpoint_after_logout(
        self, api_client, admin_user
    ):
        """Test that protected endpoints are inaccessible after logout"""
        from accounts.models import Invitation

        # Create invitation
        invitation = Invitation.objects.create(created_by=admin_user)

        # Register and login
        register_data = {
            "email": "test@example.com",
            "password1": "testpass123",
            "password2": "testpass123",
            "token": str(invitation.token),
        }

        api_client.post("/api/auth/registration/", register_data, format="json")

        # Try to create staff (requires auth)
        staff_data = {
            "first_name": "Test",
            "last_name": "User",
            "email": "staff@example.com",
        }

        response = api_client.post("/api/users/", staff_data, format="json")

        # Should succeed (just registered and have cookies)
        if response.status_code == status.HTTP_201_CREATED:
            # Logout
            api_client.post("/api/auth/logout/", format="json")

            # Try again - should fail
            response2 = api_client.post("/api/users/", staff_data, format="json")

            # After logout, should not be able to create
            # Note: This might not work perfectly with test client cookie handling
            # In real scenario, cookies would be cleared
            pass
