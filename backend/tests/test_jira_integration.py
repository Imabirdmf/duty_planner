"""
Tests for Jira integration functionality
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from planner.models import Staff, Duty, DutyAssignment
from common_app.services.jira import JiraService


@pytest.mark.django_db
class TestJiraService:
    """Tests for JiraService class"""

    def test_jira_service_initialization(self, jira_env_vars):
        """Test JiraService initializes correctly with environment variables"""
        service = JiraService()

        assert service.base_url == "https://test.atlassian.net"
        assert service.project_key == "TEST"
        assert service.parent_issue_key == "TEST-123"
        assert service.session is not None
        assert "Authorization" in service.session.headers

    @patch("common_app.services.jira.requests.Session")
    def test_create_issue_success(self, mock_session, jira_env_vars):
        """Test successful Jira issue creation"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.json.return_value = {"key": "TEST-456"}

        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = JiraService()
        service.session = mock_session_instance

        test_date = date(2024, 3, 15)
        issue_key = service.create_issue(
            date=test_date, jira_team_id="team-123", jira_account_id="acc-456"
        )

        assert issue_key == "TEST-456"
        assert mock_session_instance.post.called

        # Verify payload
        call_args = mock_session_instance.post.call_args
        payload = call_args[1]["json"]

        assert payload["fields"]["project"]["key"] == "TEST"
        assert payload["fields"]["summary"] == f"Регресс {test_date}"
        assert payload["fields"]["assignee"]["accountId"] == "acc-456"
        assert payload["fields"]["customfield_10839"]["id"] == "team-123"

    @patch("common_app.services.jira.requests.Session")
    def test_create_issue_failure(self, mock_session, jira_env_vars):
        """Test Jira issue creation failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"

        mock_session_instance = Mock()
        mock_session_instance.post.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = JiraService()
        service.session = mock_session_instance

        with pytest.raises(Exception, match="Bad Request"):
            service.create_issue(
                date=date(2024, 3, 15),
                jira_team_id="team-123",
                jira_account_id="acc-456",
            )

    @patch("common_app.services.jira.requests.Session")
    def test_update_issue_success(self, mock_session, jira_env_vars):
        """Test successful Jira issue update"""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 204

        mock_session_instance = Mock()
        mock_session_instance.put.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = JiraService()
        service.session = mock_session_instance

        service.update_issue(
            issue_key="TEST-456", jira_team_id="team-789", jira_account_id="acc-999"
        )

        assert mock_session_instance.put.called

        # Verify payload
        call_args = mock_session_instance.put.call_args
        payload = call_args[1]["json"]

        assert payload["fields"]["assignee"]["accountId"] == "acc-999"
        assert payload["fields"]["customfield_10839"]["id"] == "team-789"

    @patch("common_app.services.jira.requests.Session")
    def test_update_issue_failure(self, mock_session, jira_env_vars):
        """Test Jira issue update failure"""
        # Mock failed response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Update failed"

        mock_session_instance = Mock()
        mock_session_instance.put.return_value = mock_response
        mock_session.return_value = mock_session_instance

        service = JiraService()
        service.session = mock_session_instance

        with pytest.raises(Exception, match="Update failed"):
            service.update_issue(
                issue_key="TEST-456", jira_team_id="team-123", jira_account_id="acc-456"
            )


@pytest.mark.django_db
class TestStaffJiraFields:
    """Tests for Jira-related fields in Staff model"""

    def test_staff_has_jira_fields(self):
        """Test that Staff model has Jira fields"""
        staff = Staff.objects.create(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            jira_team_id="team-123",
            jira_account_id="acc-456",
        )

        assert staff.jira_team_id == "team-123"
        assert staff.jira_account_id == "acc-456"

    def test_staff_jira_fields_optional(self):
        """Test that Jira fields are optional"""
        staff = Staff.objects.create(
            first_name="Test", last_name="User", email="test@example.com"
        )

        assert staff.jira_team_id is None
        assert staff.jira_account_id is None


@pytest.mark.django_db
class TestDutyAssignmentJiraFields:
    """Tests for Jira-related fields in DutyAssignment model"""

    def test_duty_assignment_has_jira_fields(self, staff_user, duty_day):
        """Test that DutyAssignment has Jira fields"""
        assignment = DutyAssignment.objects.create(
            user=staff_user, duty=duty_day, jira_issue_key="TEST-123", is_synced=True
        )

        assert assignment.jira_issue_key == "TEST-123"
        assert assignment.is_synced is True

    def test_duty_assignment_jira_fields_default(self, staff_user, duty_day):
        """Test default values for Jira fields"""
        assignment = DutyAssignment.objects.create(user=staff_user, duty=duty_day)

        assert assignment.jira_issue_key is None
        assert assignment.is_synced is False


@pytest.mark.django_db
class TestManageAssignmentsJiraIntegration:
    """Tests for Jira integration in ManageAssignments service"""

    def test_create_jira_ticket_for_new_assignment(
        self, staff_with_jira, duty_day, mock_jira_service
    ):
        """Test creating Jira ticket for new assignment"""
        from planner.services.assignments import ManageAssignments

        # Create assignment without Jira key
        assignment = DutyAssignment.objects.create(user=staff_with_jira, duty=duty_day)

        service = ManageAssignments()
        # Pass duty.id, not assignment.id!
        service.create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service  # Changed from assignment.id
        )

        # Verify Jira issue was created
        mock_jira_service.create_issue.assert_called_once_with(
            duty_day.date, "team-123", "acc-456"
        )

        # Verify assignment was updated
        assignment.refresh_from_db()
        assert assignment.jira_issue_key == "TEST-789"
        assert assignment.is_synced is True

    def test_update_jira_ticket_for_existing_unsynced(
        self, staff_with_jira, duty_day, mock_jira_service
    ):
        """Test updating existing Jira ticket when not synced"""
        from planner.services.assignments import ManageAssignments

        # Create assignment with Jira key but not synced
        assignment = DutyAssignment.objects.create(
            user=staff_with_jira,
            duty=duty_day,
            jira_issue_key="TEST-456",
            is_synced=False,
        )

        service = ManageAssignments()
        # Pass duty.id, not assignment.id!
        service.create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service  # Changed from assignment.id
        )

        # Verify Jira issue was updated (not created)
        mock_jira_service.update_issue.assert_called_once_with(
            "TEST-456", "team-123", "acc-456"
        )

        # Verify assignment was marked as synced
        assignment.refresh_from_db()
        assert assignment.is_synced is True

    def test_skip_already_synced_assignment(
        self, staff_with_jira, duty_day, mock_jira_service
    ):
        """Test that already synced assignments are skipped"""
        from planner.services.assignments import ManageAssignments

        # Create assignment that's already synced
        assignment = DutyAssignment.objects.create(
            user=staff_with_jira,
            duty=duty_day,
            jira_issue_key="TEST-456",
            is_synced=True,
        )

        service = ManageAssignments()
        # Pass duty.id, not assignment.id!
        service.create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service  # Changed from assignment.id
        )

        # Verify no Jira calls were made
        mock_jira_service.create_issue.assert_not_called()
        mock_jira_service.update_issue.assert_not_called()


@pytest.mark.django_db
class TestJiraSyncView:
    """Tests for JiraSyncView endpoint"""

    @patch("planner.views.JiraService")
    def test_jira_sync_requires_authentication(
        self, mock_jira_service_class, api_client, jira_env_vars
    ):
        """Test that Jira sync requires authentication"""
        data = {"duty_ids": [1, 2, 3]}

        response = api_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    @patch("planner.views.JiraService")
    def test_jira_sync_success(
        self,
        mock_jira_service_class,
        authenticated_client,
        staff_with_jira,
        duty_day,
        jira_env_vars,
    ):
        """Test successful Jira sync"""
        # Create assignment
        assignment = DutyAssignment.objects.create(user=staff_with_jira, duty=duty_day)

        # Mock JiraService
        mock_jira_instance = Mock()
        mock_jira_instance.create_issue.return_value = "TEST-789"
        mock_jira_service_class.return_value = mock_jira_instance

        # Pass duty.id, not assignment.id!
        data = {"duty_ids": [duty_day.id]}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] == "Everything is synced with Jira"

    @patch("planner.views.JiraService")
    def test_jira_sync_missing_duty_ids(
        self, mock_jira_service_class, authenticated_client, jira_env_vars
    ):
        """Test Jira sync with missing duty_ids"""
        data = {}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "error" in response.data

    @patch("planner.views.JiraService")
    def test_jira_sync_empty_duty_ids(
        self, mock_jira_service_class, authenticated_client, jira_env_vars
    ):
        """Test Jira sync with empty duty_ids list"""
        data = {"duty_ids": []}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("planner.views.JiraService")
    def test_jira_sync_handles_exceptions(
        self,
        mock_jira_service_class,
        authenticated_client,
        staff_with_jira,
        duty_day,
        jira_env_vars,
    ):
        """Test Jira sync handles exceptions properly"""
        # Create assignment
        assignment = DutyAssignment.objects.create(user=staff_with_jira, duty=duty_day)

        # Mock JiraService to raise exception
        mock_jira_instance = Mock()
        mock_jira_instance.create_issue.side_effect = Exception("Jira API error")
        mock_jira_service_class.return_value = mock_jira_instance

        # Pass duty.id, not assignment.id!
        data = {"duty_ids": [duty_day.id]}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "error" in response.data


@pytest.mark.django_db
class TestBulkDeleteAction:
    """Tests for bulk_delete action on DutyAssignmentViewSet"""

    def test_bulk_delete_requires_authentication(self, api_client, duty_days):
        """Test that bulk delete requires authentication"""
        duty_ids = [d.id for d in duty_days[:3]]
        data = {"duty_ids": duty_ids}

        response = api_client.post("/api/duties/bulk_delete/", data, format="json")

        assert response.status_code in [
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_bulk_delete_success(self, authenticated_client, duty_days):
        """Test successful bulk deletion of duties"""
        duty_ids = [d.id for d in duty_days[:3]]
        data = {"duty_ids": duty_ids}

        initial_count = Duty.objects.count()

        response = authenticated_client.post(
            "/api/duties/bulk_delete/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_duty_count"] == 3
        assert Duty.objects.count() == initial_count - 3

    def test_bulk_delete_with_assignments(self, authenticated_client, duty_assignments):
        """Test bulk delete removes assignments via CASCADE"""
        duty_ids = [da.duty.id for da in duty_assignments[:2]]
        data = {"duty_ids": duty_ids}

        initial_assignment_count = DutyAssignment.objects.count()

        response = authenticated_client.post(
            "/api/duties/bulk_delete/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        # Assignments should be deleted via CASCADE
        assert DutyAssignment.objects.count() < initial_assignment_count

    def test_bulk_delete_empty_list(self, authenticated_client):
        """Test bulk delete with empty duty_ids list"""
        data = {"duty_ids": []}

        response = authenticated_client.post(
            "/api/duties/bulk_delete/", data, format="json"
        )

        # Should handle gracefully - either 400 or delete 0
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    def test_bulk_delete_nonexistent_ids(self, authenticated_client):
        """Test bulk delete with non-existent IDs"""
        data = {"duty_ids": [9999, 10000]}

        response = authenticated_client.post(
            "/api/duties/bulk_delete/", data, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["deleted_duty_count"] == None
