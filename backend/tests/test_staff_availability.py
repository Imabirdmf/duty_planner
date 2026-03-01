"""
Tests for StaffAvailability service
"""

import pytest
from planner.services.staff_availability import StaffAvailability


@pytest.mark.django_db
class TestStaffAvailability:
    """Tests for StaffAvailability class"""

    @pytest.fixture
    def availability(self):
        return StaffAvailability()

    def test_is_unavailable_has_day_off(self, availability, day_off):
        """Test is_unavailable returns True when staff has day off"""
        result = availability.is_unavailable(day_off.user.id, day_off.date)
        assert result is True

    def test_is_unavailable_no_conflicts(self, availability, staff_user, tomorrow):
        """Test is_unavailable returns False when staff is available"""
        result = availability.is_unavailable(staff_user.id, tomorrow)
        assert result is False

    def test_has_days_off_true(self, availability, day_off):
        """Test has_days_off returns True"""
        result = availability.has_days_off(day_off.user.id, day_off.date)
        assert result is True

    def test_has_days_off_false(self, availability, staff_user, tomorrow):
        """Test has_days_off returns False"""
        result = availability.has_days_off(staff_user.id, tomorrow)
        assert result is False

    def test_has_previous_duty_true(self, availability, duty_days, staff_users):
        """Test has_previous_duty returns True when user had previous duty"""
        from planner.models import DutyAssignment

        # Assign user to first duty
        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0])

        # Check if user has previous duty for second day
        result = availability.has_previous_duty(staff_users[0].id, duty_days[1].date)
        assert result is True

    def test_has_previous_duty_false(self, availability, duty_days, staff_users):
        """Test has_previous_duty returns False"""
        result = availability.has_previous_duty(staff_users[0].id, duty_days[1].date)
        assert result is False

    def test_has_previous_duty_no_previous_duties(
        self, availability, duty_day, staff_user
    ):
        """Test has_previous_duty when no previous duties exist"""
        result = availability.has_previous_duty(staff_user.id, duty_day.date)
        assert result is False

    def test_has_current_duty_true(self, availability, duty_assignment):
        """Test has_current_duty returns True"""
        result = availability.has_current_duty(
            duty_assignment.user.id, duty_assignment.duty.date
        )
        assert result is True

    def test_has_current_duty_false(self, availability, staff_user, duty_day):
        """Test has_current_duty returns False"""
        result = availability.has_current_duty(staff_user.id, duty_day.date)
        assert result is False

    def test_is_unavailable_has_previous_duty(
        self, availability, duty_days, staff_users
    ):
        """Test is_unavailable returns True when user has previous duty"""
        from planner.models import DutyAssignment

        DutyAssignment.objects.create(user=staff_users[0], duty=duty_days[0])

        result = availability.is_unavailable(staff_users[0].id, duty_days[1].date)
        assert result is True

    def test_is_unavailable_has_current_duty(self, availability, duty_assignment):
        """Test is_unavailable returns True when user already has current duty"""
        result = availability.is_unavailable(
            duty_assignment.user.id, duty_assignment.duty.date
        )
        assert result is True
