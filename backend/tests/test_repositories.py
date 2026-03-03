import pytest
from django.db import IntegrityError
from planner.models import Staff, DaysOff, Duty, DutyAssignment
from planner.services.repositories.staff_repository import StaffRepository
from planner.services.repositories.days_off_repository import DaysOffRepository
from planner.services.repositories.duty_repository import DutyRepository
from planner.services.repositories.duty_assignment_repository import (
    DutyAssignmentRepository,
)
import logging

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestStaffRepository:
    """Tests for StaffRepository"""

    @pytest.fixture
    def repository(self):
        return StaffRepository()

    def test_get_all_empty(self, repository):
        """Test getting all staff when DB is empty"""
        result = repository.get_all()
        assert result.count() == 0

    def test_get_all_with_data(self, repository, staff_users):
        """Test getting all staff members"""
        result = repository.get_all()
        assert result.count() == len(staff_users)

    def test_get_by_id_success(self, repository, staff_user):
        """Test getting staff by ID"""
        result = repository.get_by_id(staff_user.id)
        assert result.id == staff_user.id
        assert result.email == staff_user.email

    def test_get_by_id_not_found(self, repository):
        """Test getting non-existent staff"""
        with pytest.raises(Staff.DoesNotExist):
            repository.get_by_id(99999)

    def test_create_staff(self, repository):
        """Test creating new staff"""
        staff = repository.create(
            first_name="Test", last_name="User", email="test@example.com", priority=0
        )
        assert staff.id is not None
        assert Staff.objects.count() == 1

    def test_update_staff(self, repository, staff_user):
        """Test updating staff"""
        updated = repository.update(staff_user.id, first_name="Updated")
        assert updated.first_name == "Updated"

    def test_delete_staff(self, repository, staff_user):
        """Test deleting staff"""
        repository.delete(staff_user.id)
        assert Staff.objects.count() == 0

    def test_update_priority_with_value(self, repository, staff_user):
        """Test updating priority with specific value"""
        repository.update_priority(staff_user.id, value=5)
        staff_user.refresh_from_db()
        assert staff_user.priority == 5

    def test_update_priority_with_diff(self, repository, staff_user):
        """Test updating priority with diff"""
        initial = staff_user.priority
        repository.update_priority(staff_user.id, diff=3)
        staff_user.refresh_from_db()
        assert staff_user.priority == initial + 3

    def test_update_priority_negative_value_becomes_zero(self, repository, staff_user):
        """Test that negative priority becomes 0 (Greatest function)"""
        repository.update_priority(staff_user.id, value=-5)
        staff_user.refresh_from_db()
        assert staff_user.priority == 0

    def test_update_priority_negative_diff_becomes_zero(self, repository, staff_user):
        """Test that priority doesn't go below 0 with negative diff"""
        staff_user.priority = 1
        staff_user.save()
        repository.update_priority(staff_user.id, diff=-10)
        staff_user.refresh_from_db()
        assert staff_user.priority == 0

    def test_get_minimum_priority(self, repository, staff_users):
        """Test getting minimum priority"""
        # Set different priorities
        Staff.objects.filter(id=staff_users[0].id).update(priority=5)
        Staff.objects.filter(id=staff_users[1].id).update(priority=3)
        Staff.objects.filter(id=staff_users[2].id).update(priority=7)
        Staff.objects.filter(id=staff_users[4].id).update(priority=3)

        min_priority = repository.get_minimum_priority()
        assert min_priority == 3

    def test_get_minimum_priority_no_positive_priorities(self, repository, staff_users):
        """Test get_minimum_priority when all priorities are 0"""
        Staff.objects.all().update(priority=0)
        min_priority = repository.get_minimum_priority()
        assert min_priority is None

    def test_set_minimum_priority_for_all(self, repository, staff_users):
        """Test normalizing priorities by subtracting minimum"""
        # Set priorities: 5, 6, 7, 8
        for i, user in enumerate(staff_users):
            Staff.objects.filter(id=user.id).update(priority=i + 5)

        repository.set_minimum_priority_for_all(5)

        priorities = list(
            Staff.objects.filter(priority__gt=0)
            .values_list("priority", flat=True)
            .order_by("priority")
        )
        logger.info("priorities: %s", priorities)
        assert min(priorities) == 1
        assert priorities == [1, 2, 3, 4]


@pytest.mark.django_db
class TestDaysOffRepository:
    """Tests for DaysOffRepository"""

    @pytest.fixture
    def repository(self):
        return DaysOffRepository()

    def test_get_all(self, repository, days_off_multiple):
        """Test getting all days off"""
        result = repository.get_all()
        assert result.count() == len(days_off_multiple)

    def test_create_day_off(self, repository, staff_user, tomorrow):
        """Test creating day off"""
        day_off = repository.create(user=staff_user, date=tomorrow)
        assert day_off.id is not None
        assert DaysOff.objects.count() == 1

    def test_exists_for_user_in_date_true(self, repository, day_off):
        """Test exists_for_user_in_date returns True"""
        result = repository.exists_for_user_in_date(day_off.user.id, day_off.date)
        assert result is True

    def test_exists_for_user_in_date_false(self, repository, staff_user, tomorrow):
        """Test exists_for_user_in_date returns False"""
        result = repository.exists_for_user_in_date(staff_user.id, tomorrow)
        assert result is False

    def test_get_list_of_days_off(self, repository, days_off_multiple, date_range):
        """Test getting days off within date range"""
        result = repository.get_list_of_days_off(date_range["start"], date_range["end"])
        assert result.count() == len(days_off_multiple)

    def test_delete_day_off(self, repository, day_off):
        """Test deleting day off"""
        repository.delete(day_off.id)
        assert DaysOff.objects.count() == 0


@pytest.mark.django_db
class TestDutyRepository:
    """Tests for DutyRepository"""

    @pytest.fixture
    def repository(self):
        return DutyRepository()

    def test_get_all(self, repository, duty_days):
        """Test getting all duties"""
        result = repository.get_all()
        assert result.count() == len(duty_days)

    def test_create_duty(self, repository, tomorrow):
        """Test creating duty"""
        duty = repository.create(date=tomorrow)
        assert duty.id is not None
        assert Duty.objects.count() == 1

    def test_get_previous_duty_exists(self, repository, duty_days):
        """Test getting previous duty when it exists"""
        target_date = duty_days[2].date
        previous_duty_id = repository.get_previous_duty(target_date)
        assert previous_duty_id == duty_days[1].id

    def test_get_previous_duty_not_exists(self, repository, duty_days):
        """Test getting previous duty when none exists"""
        first_date = duty_days[0].date
        previous_duty_id = repository.get_previous_duty(first_date)
        assert previous_duty_id is None

    def test_get_list_of_duties(self, repository, duty_days, date_range):
        """Test getting duties within date range"""
        result = repository.get_list_of_duties(date_range["start"], date_range["end"])
        assert result.count() == len(duty_days)

    def test_get_first_element_by_date(self, repository, duty_day):
        """Test getting duty by date"""
        result = repository.get_first_element_by_date(duty_day.date)
        assert result.id == duty_day.id

    def test_get_first_element_by_date_not_found(self, repository, tomorrow):
        """Test getting duty by non-existent date"""
        result = repository.get_first_element_by_date(tomorrow)
        assert result is None

    def test_get_list_of_duties_ordered_by_date(
        self, repository, duty_days, date_range
    ):
        """Test getting duties ordered by date"""
        result = repository.get_list_of_duties(
            date_range["start"], date_range["end"], ordered=True
        )
        dates = list(result.values_list("date", flat=True))
        assert dates == sorted(dates)

    def test_save_duty_days(self, repository, date_range):
        """Test bulk creating duty days"""
        dates = date_range["dates"]
        result = repository.save_duty_days(dates)

        assert len(result) == len(dates)
        assert Duty.objects.count() == len(dates)

    def test_save_duty_days_idempotent(self, repository, date_range):
        """Test that save_duty_days is idempotent"""
        dates = date_range["dates"]
        repository.save_duty_days(dates)
        count1 = Duty.objects.count()

        repository.save_duty_days(dates)
        count2 = Duty.objects.count()

        assert count1 == count2


@pytest.mark.django_db
class TestDutyAssignmentRepository:
    """Tests for DutyAssignmentRepository"""

    @pytest.fixture
    def repository(self):
        return DutyAssignmentRepository()

    def test_get_all(self, repository, duty_assignments):
        """Test getting all duty assignments"""
        result = repository.get_all()
        assert result.count() == len(duty_assignments)

    def test_create_assignment(self, repository, staff_user, duty_day):
        """Test creating duty assignment"""
        assignment = repository.create(user_id=staff_user.id, duty=duty_day)
        assert assignment.id is not None
        assert DutyAssignment.objects.count() == 1

    def test_user_has_assignment_for_duty_id_true(self, repository, duty_assignment):
        """Test user_has_assignment_for_duty_id returns True"""
        result = repository.user_has_assignment_for_duty_id(
            duty_assignment.user.id, duty_assignment.duty.id
        )
        assert result is True

    def test_user_has_assignment_for_duty_id_false(
        self, repository, staff_user, duty_day
    ):
        """Test user_has_assignment_for_duty_id returns False"""
        result = repository.user_has_assignment_for_duty_id(staff_user.id, duty_day.id)
        assert result is False

    def test_get_list_of_duty_assignment(
        self, repository, duty_assignments, date_range
    ):
        """Test getting assignments within date range"""
        result = repository.get_list_of_duty_assignment(
            date_range["start"], date_range["end"]
        )
        assert result.count() == len(duty_assignments)

    def test_get_assignment_by_duty_and_user(self, repository, duty_assignment):
        """Test getting assignment by duty and user"""
        result = repository.get_assignment_by_duty_and_user(
            duty_assignment.duty.id, duty_assignment.user.id
        )
        assert result.id == duty_assignment.id

    def test_get_first_element_by_user(self, repository, duty_assignment):
        """Test getting assignment by user and date"""
        result = repository.get_first_element_by_user(
            duty_assignment.duty.date, duty_assignment.user.id
        )
        assert result.id == duty_assignment.id

    def test_get_count_by_duty_id(self, repository, duty_assignments, duty_days):
        """Test counting assignments for a duty"""
        # duty_days[0] has 2 assignments (from fixture)
        count = repository.get_count_by_duty_id(duty_days[0].id)
        assert count == 2

    def test_get_users_for_duty(self, repository, duty_assignments, duty_days):
        """Test getting users assigned to a duty"""
        users = repository.get_users_for_duty(duty_days[0].id)
        assert len(users) == 2
        assert all(isinstance(u, Staff) for u in users)

    def test_delete_assignment(self, repository, duty_assignment):
        """Test deleting assignment"""
        repository.delete(duty_assignment.id)
        assert DutyAssignment.objects.count() == 0
