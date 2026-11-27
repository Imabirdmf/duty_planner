"""
Tests for Jira integration functionality
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock, patch, MagicMock
from rest_framework import status
from planner.models import Staff, Duty, DutyAssignment
import requests
from common_app.services.jira import (
    BULK_CREATE_LIMIT,
    BulkCreateResult,
    IssueData,
    JiraService,
)


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

    @staticmethod
    def _service_with_post(*responses):
        service = JiraService()
        service.session = Mock()
        service.session.post.side_effect = list(responses)
        return service

    @staticmethod
    def _response(status_code, body):
        response = Mock()
        response.status_code = status_code
        response.json.return_value = body
        response.text = str(body)
        return response

    @staticmethod
    def _issues(n, day=None):
        day = day or date.today()
        return [
            IssueData(day + timedelta(days=i), "team", f"acc-{i}") for i in range(n)
        ]

    def test_bulk_create_all_success(self, jira_env_vars):
        service = self._service_with_post(
            self._response(
                201,
                {"issues": [{"key": "TEST-1"}, {"key": "TEST-2"}], "errors": []},
            )
        )

        result = service.bulk_create_issues(self._issues(2))

        assert result.keys == {0: "TEST-1", 1: "TEST-2"}
        assert result.errors == {}
        call = service.session.post.call_args
        assert call.kwargs["url"] == "https://test.atlassian.net/rest/api/3/issue/bulk"
        updates = call.kwargs["json"]["issueUpdates"]
        assert len(updates) == 2
        assert updates[0]["fields"]["project"]["key"] == "TEST"
        assert updates[1]["fields"]["assignee"]["accountId"] == "acc-1"

    def test_bulk_create_partial_failure_maps_keys_by_index(self, jira_env_vars):
        service = self._service_with_post(
            self._response(
                201,
                {
                    "issues": [{"key": "TEST-1"}, {"key": "TEST-3"}],
                    "errors": [
                        {
                            "failedElementNumber": 1,
                            "status": 400,
                            "elementErrors": {
                                "errorMessages": [],
                                "errors": {"assignee": "User cannot be assigned"},
                            },
                        }
                    ],
                },
            )
        )

        result = service.bulk_create_issues(self._issues(3))

        assert result.keys == {0: "TEST-1", 2: "TEST-3"}
        assert result.errors == {1: "assignee: User cannot be assigned"}

    def test_bulk_create_all_failed_400(self, jira_env_vars):
        service = self._service_with_post(
            self._response(
                400,
                {
                    "issues": [],
                    "errors": [
                        {
                            "failedElementNumber": 0,
                            "elementErrors": {"errorMessages": ["Bad project"]},
                        }
                    ],
                },
            )
        )

        result = service.bulk_create_issues(self._issues(1))

        assert result.keys == {}
        assert result.errors == {0: "Bad project"}

    def test_bulk_create_auth_error_marks_whole_chunk(self, jira_env_vars):
        service = self._service_with_post(
            self._response(401, {"errorMessages": ["Unauthorized"]})
        )

        result = service.bulk_create_issues(self._issues(2))

        assert result.keys == {}
        assert result.errors == {0: "Unauthorized", 1: "Unauthorized"}

    def test_bulk_create_network_error_marks_whole_chunk(self, jira_env_vars):
        service = JiraService()
        service.session = Mock()
        service.session.post.side_effect = requests.ConnectionError("boom")

        result = service.bulk_create_issues(self._issues(2))

        assert result.errors == {0: "boom", 1: "boom"}

    def test_bulk_create_chunks_and_keeps_earlier_chunk_on_failure(self, jira_env_vars):
        n = BULK_CREATE_LIMIT + 1
        first = self._response(
            201,
            {
                "issues": [{"key": f"TEST-{i}"} for i in range(BULK_CREATE_LIMIT)],
                "errors": [],
            },
        )
        second = self._response(500, {"errorMessages": ["Jira is down"]})
        service = self._service_with_post(first, second)

        result = service.bulk_create_issues(self._issues(n))

        assert service.session.post.call_count == 2
        assert len(result.keys) == BULK_CREATE_LIMIT
        assert result.errors == {BULK_CREATE_LIMIT: "Jira is down"}

    def test_bulk_create_empty_makes_no_request(self, jira_env_vars):
        service = self._service_with_post()

        result = service.bulk_create_issues([])

        assert result == BulkCreateResult()
        service.session.post.assert_not_called()

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
        assert payload["fields"]["customfield_10382"]["accountId"] == "acc-999"
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

        assert staff.jira_team_id is ""
        assert staff.jira_account_id is ""


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

        assert assignment.jira_issue_key is ""
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

        # Verify Jira issue was created via bulk API
        mock_jira_service.bulk_create_issues.assert_called_once_with(
            [IssueData(duty_day.date, "team-123", "acc-456")]
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
        mock_jira_service.bulk_create_issues.assert_not_called()
        mock_jira_service.update_issue.assert_not_called()

    def test_replaced_assignee_is_pushed_to_existing_issue(
        self, staff_with_jira, staff_user, duty_day, mock_jira_service
    ):
        """Swapping the duty person on the front re-targets the linked issue"""
        from planner.services.assignments import ManageAssignments

        staff_user.jira_account_id = "acc-new"
        staff_user.jira_team_id = "team-new"
        staff_user.save()
        assignment = DutyAssignment.objects.create(
            user=staff_with_jira, duty=duty_day, jira_issue_key="TEST-1", is_synced=True
        )
        service = ManageAssignments()

        service.make_assignment(duty_day.date, staff_with_jira.id, staff_user.id)
        result = service.create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service
        )

        mock_jira_service.update_issue.assert_called_once_with(
            "TEST-1", "team-new", "acc-new"
        )
        mock_jira_service.bulk_create_issues.assert_not_called()
        assert result["updated"] == 1
        assignment.refresh_from_db()
        assert (assignment.user_id, assignment.is_synced) == (staff_user.id, True)

    def test_sync_result_reports_partial_failure(
        self, staff_with_jira, staff_user, duty_day, mock_jira_service
    ):
        """Created, updated and failed assignments are all reported"""
        from planner.services.assignments import ManageAssignments

        ok = DutyAssignment.objects.create(user=staff_with_jira, duty=duty_day)
        bad = DutyAssignment.objects.create(user=staff_user, duty=duty_day)
        # Fail only the issue for staff_user (no Jira account), wherever it sits.
        mock_jira_service.bulk_create_issues.side_effect = lambda issues: (
            BulkCreateResult(
                keys={
                    i: "TEST-1"
                    for i, x in enumerate(issues)
                    if x.jira_account_id == "acc-456"
                },
                errors={
                    i: "assignee: invalid"
                    for i, x in enumerate(issues)
                    if x.jira_account_id != "acc-456"
                },
            )
        )

        result = ManageAssignments().create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service
        )

        assert result["created"] == 1
        assert result["updated"] == 0
        assert result["skipped"] == 0
        assert result["failed"] == [
            {
                "date": duty_day.date.isoformat(),
                "user": staff_user.full_name,
                "message": "assignee: invalid",
            }
        ]
        ok.refresh_from_db()
        bad.refresh_from_db()
        assert (ok.jira_issue_key, ok.is_synced) == ("TEST-1", True)
        assert (bad.jira_issue_key, bad.is_synced) == ("", False)

    def test_sync_result_reports_update_failure(
        self, staff_with_jira, duty_day, mock_jira_service
    ):
        from planner.services.assignments import ManageAssignments

        assignment = DutyAssignment.objects.create(
            user=staff_with_jira, duty=duty_day, jira_issue_key="TEST-1"
        )
        mock_jira_service.update_issue.side_effect = requests.HTTPError("not found")

        result = ManageAssignments().create_or_update_jira_ticket(
            duty_ids=[duty_day.id], jira=mock_jira_service
        )

        assert result["updated"] == 0
        assert result["failed"][0]["message"] == "not found"
        assignment.refresh_from_db()
        assert assignment.is_synced is False


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
        mock_jira_instance.bulk_create_issues.return_value = BulkCreateResult(
            keys={0: "TEST-789"}
        )
        mock_jira_service_class.return_value = mock_jira_instance

        # Pass duty.id, not assignment.id!
        data = {"duty_ids": [duty_day.id]}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Synced with Jira: 1 created"
        assert response.data["created"] == 1
        assert response.data["failed"] == []

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
        mock_jira_instance.bulk_create_issues.side_effect = Exception("Jira API error")
        mock_jira_service_class.return_value = mock_jira_instance

        # Pass duty.id, not assignment.id!
        data = {"duty_ids": [duty_day.id]}

        response = authenticated_client.post("/api/jira/sync/", data, format="json")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.data["error"] == "Jira sync failed: Jira API error"

    @patch("planner.views.JiraService")
    def test_jira_sync_reports_failures_with_200(
        self,
        mock_jira_service_class,
        authenticated_client,
        staff_with_jira,
        duty_day,
        jira_env_vars,
    ):
        """Per-assignment Jira errors come back in `failed`, not as a 500"""
        DutyAssignment.objects.create(user=staff_with_jira, duty=duty_day)
        mock_jira_instance = Mock()
        mock_jira_instance.bulk_create_issues.return_value = BulkCreateResult(
            errors={0: "Bad project"}
        )
        mock_jira_service_class.return_value = mock_jira_instance

        response = authenticated_client.post(
            "/api/jira/sync/", {"duty_ids": [duty_day.id]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] is None
        assert response.data["failed"][0]["message"] == "Bad project"

    @patch("planner.views.JiraService")
    def test_jira_sync_nothing_to_do(
        self,
        mock_jira_service_class,
        authenticated_client,
        staff_with_jira,
        duty_day,
        jira_env_vars,
    ):
        DutyAssignment.objects.create(
            user=staff_with_jira, duty=duty_day, jira_issue_key="T-1", is_synced=True
        )

        response = authenticated_client.post(
            "/api/jira/sync/", {"duty_ids": [duty_day.id]}, format="json"
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Everything is already synced with Jira"
        assert response.data["skipped"] == 1


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
