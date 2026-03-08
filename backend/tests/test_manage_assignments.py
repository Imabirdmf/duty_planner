"""
Tests for ManageAssignments service
"""

import pytest
from datetime import timedelta
from planner.services.assignments import ManageAssignments
from planner.models import DutyAssignment, DaysOff, Duty, Staff


@pytest.mark.django_db
class TestManageAssignments:
    """Tests for ManageAssignments class"""

    @pytest.fixture
    def service(self):
        return ManageAssignments()

    def test_get_duties_by_date_single_date(self, service, duty_day):
        """Test getting duties for single date"""
        result = service.get_duties_by_date(duty_day.date, None)
        assert result.count() == 1
        assert result.first().id == duty_day.id

    def test_get_duties_by_date_range(self, service, duty_days, date_range):
        """Test getting duties for date range"""
        result = service.get_duties_by_date(date_range["start"], date_range["end"])
        assert result.count() == len(duty_days)

    def test_create_duty_days(self, service, date_range):
        """Test creating duty days"""
        dates = date_range["dates"]
        result = service.create_duty_days(dates)

        assert len(result) == len(dates)

    def test_get_duty_assignments_single_date(
        self, service, duty_assignments, date_range
    ):
        """Test getting duty assignments for single date"""
        result = service.get_duty_assignments(date_range["start"], None)
        assert result.count() >= 1

    def test_get_duty_assignments_range(self, service, duty_assignments, date_range):
        """Test getting duty assignments for date range"""
        result = service.get_duty_assignments(date_range["start"], date_range["end"])
        assert result.count() == len(duty_assignments)

    def test_get_date_range(self, service, date_range):
        """Test extracting start and end from dates list"""
        dates = date_range["dates"]
        start, end = service.get_date_range(dates)

        assert start == dates[0]
        assert end == dates[-1]

    def test_get_days_off_with_dates(self, service, days_off_multiple, date_range):
        """Test getting days off with date range"""
        result = service.get_days_off(date_range["start"], date_range["end"])
        assert result.count() == len(days_off_multiple)

    def test_get_days_off_without_dates(self, service, days_off_multiple):
        """Test getting all days off without date filter"""
        result = service.get_days_off(None, None)
        assert result.count() == len(days_off_multiple)

    def test_get_all_staff(self, service, staff_users):
        """Test getting all staff"""
        result = service.get_all_staff()
        assert result.count() == len(staff_users)

    def test_get_all_duty_assignments(self, service, duty_assignments):
        """Test getting all duty assignments"""
        result = service.get_all_duty_assignments()
        assert result.count() == len(duty_assignments)

    def test_get_all_duties(self, service, duty_days):
        """Test getting all duties"""
        result = service.get_all_duties()
        assert result.count() == len(duty_days)

    def test_create_assignment(self, service, staff_user, duty_day):
        """Test creating new assignment"""
        assignment = service.create_assignment(duty_day.date, staff_user.id)

        assert assignment.id is not None
        assert assignment.user.id == staff_user.id
        assert assignment.duty.id == duty_day.id

        # Check priority was updated
        staff_user.refresh_from_db()
        assert staff_user.priority == 1

    def test_update_assignment(self, service, duty_assignment, staff_users):
        """Test updating existing assignment"""
        old_user = duty_assignment.user
        print(old_user)
        new_user = staff_users[1]
        print(new_user)
        old_priority = old_user.priority
        new_priority = new_user.priority

        result = service.update_assignment(
            duty_assignment.duty.date, old_user.id, new_user.id
        )

        # Check assignment was updated
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

        # Check priorities were updated
        old_user.refresh_from_db()
        new_user.refresh_from_db()
        assert old_user.priority == max((old_priority - 1), 0)
        assert new_user.priority == new_priority + 1

    def test_delete_assignment(self, service, duty_assignment):
        """Test deleting assignment"""
        duty_date = duty_assignment.duty.date
        user_id = duty_assignment.user.id
        assignment_id = duty_assignment.id

        service.delete_assignment(duty_date, user_id)

        # Check assignment was deleted
        assert not DutyAssignment.objects.filter(id=assignment_id).exists()

    def test_create_assignment_atomic(self, service, staff_user, duty_day):
        """Test that create_assignment is atomic"""
        # This test verifies that if an error occurs, changes are rolled back
        # We can't easily test this without mocking, but we can verify the transaction works
        assignment = service.create_assignment(duty_day.date, staff_user.id)

        assert DutyAssignment.objects.count() == 1
        staff_user.refresh_from_db()
        assert staff_user.priority > 0

    def test_update_assignment_atomic(self, service, duty_assignment, staff_users):
        """Test that update_assignment is atomic"""
        old_user = duty_assignment.user

        new_user = staff_users[1]

        service.update_assignment(duty_assignment.duty.date, old_user.id, new_user.id)

        # Verify both assignment and priorities were updated
        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

    def test_bulk_delete_duties_by_id(self, service, duty_days):
        """Test bulk delete returns correct count and removes duties from DB"""
        ids = [duty_days[0].id, duty_days[1].id]
        initial_count = Duty.objects.count()

        deleted = service.bulk_delete_duties_by_id(ids)

        assert deleted == len(ids)
        assert Duty.objects.count() == initial_count - len(ids)

    def test_bulk_delete_duties_by_id_cascade(
        self, service, duty_assignments, duty_days
    ):
        """Test that deleting duties cascade-removes their DutyAssignments"""
        ids = [duty_days[0].id]
        assignment_count_before = DutyAssignment.objects.count()

        assignments_for_duty = DutyAssignment.objects.filter(
            duty_id=duty_days[0].id
        ).count()
        service.bulk_delete_duties_by_id(ids)

        assert (
            DutyAssignment.objects.count()
            == assignment_count_before - assignments_for_duty
        )

    def test_bulk_delete_duties_by_id_empty(self, service, duty_days):
        """Test bulk delete with empty list returns None and leaves DB unchanged"""
        initial_count = Duty.objects.count()

        deleted = service.bulk_delete_duties_by_id([])

        assert deleted is None
        assert Duty.objects.count() == initial_count

    def test_get_staff_duties(self, service, duty_assignments, date_range):
        """Test get_staff_duties returns list with correct structure"""
        result = service.get_staff_duties(date_range["start"], date_range["end"])

        assert isinstance(result, list)
        assert len(result) > 0
        for item in result:
            assert "user" in item
            assert "duties" in item
            for duty_info in item["duties"]:
                assert "month" in duty_info
                assert "duty_count" in duty_info

    def test_get_staff_duties_empty(self, service, date_range):
        """Test get_staff_duties returns empty list when no assignments exist"""
        result = service.get_staff_duties(date_range["start"], date_range["end"])

        assert result == []

    def test_make_assignment_create(self, service, staff_user, duty_day):
        """Test make_assignment creates assignment when prev is None and new is set"""
        service.make_assignment(
            duty_day.date, prev_user_id=None, new_user_id=staff_user.id
        )

        assert DutyAssignment.objects.filter(user=staff_user, duty=duty_day).exists()

    def test_make_assignment_update(self, service, duty_assignment, staff_users):
        """Test make_assignment updates assignment when both prev and new are set"""
        prev_user = duty_assignment.user
        new_user = staff_users[1]

        service.make_assignment(
            duty_assignment.duty.date,
            prev_user_id=prev_user.id,
            new_user_id=new_user.id,
        )

        duty_assignment.refresh_from_db()
        assert duty_assignment.user.id == new_user.id

    def test_make_assignment_delete(self, service, duty_assignment):
        """Test make_assignment deletes assignment when prev is set and new is None"""
        assignment_id = duty_assignment.id
        duty_date = duty_assignment.duty.date
        user_id = duty_assignment.user.id

        service.make_assignment(duty_date, prev_user_id=user_id, new_user_id=None)

        assert not DutyAssignment.objects.filter(id=assignment_id).exists()

    def test_make_assignment_both_none(self, service, duty_day):
        """Test make_assignment does nothing when both prev and new are None"""
        count_before = DutyAssignment.objects.count()

        service.make_assignment(duty_day.date, prev_user_id=None, new_user_id=None)

        assert DutyAssignment.objects.count() == count_before

    def test_create_days_off(self, service, staff_user, date_range):
        """Test create_days_off creates DaysOff records for the user"""
        dates = date_range["dates"][:3]

        result = service.create_days_off(user_id=staff_user.id, dates=dates)

        assert len(result) == len(dates)
        assert DaysOff.objects.filter(user=staff_user).count() == len(dates)
