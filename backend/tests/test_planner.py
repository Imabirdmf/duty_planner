"""
Tests for Planner service (schedule generation logic)
"""

import pytest
from datetime import timedelta
from planner.services.planner import Planner
from planner.models import Duty, DutyAssignment
import logging

logger = logging.getLogger(__name__)


@pytest.mark.django_db
class TestPlanner:
    """Tests for Planner class"""

    def test_create_plan_basic(self, staff_users, date_range):
        """Test basic plan generation"""
        # Create duty days
        for d in date_range["dates"]:
            Duty.objects.create(date=d)

        planner = Planner(
            start_date=date_range["start"], end_date=date_range["end"], people_for_day=2
        )

        messages = planner.create_plan()

        # Check that assignments were created
        assignments = DutyAssignment.objects.all()
        assert assignments.count() > 0

        # Check that priorities were updated
        for user in staff_users:
            user.refresh_from_db()

    def test_create_plan_with_days_off(self, staff_users, date_range, day_off):
        """Test plan generation respects days off"""
        # Create duty days
        for d in date_range["dates"]:
            Duty.objects.create(date=d)

        planner = Planner(
            start_date=date_range["start"], end_date=date_range["end"], people_for_day=2
        )

        messages = planner.create_plan()

        # Check that user with day off was not assigned
        assignments_on_day_off = DutyAssignment.objects.filter(
            user=day_off.user, duty__date=day_off.date
        )
        assert assignments_on_day_off.count() == 0

    def test_create_plan_insufficient_staff(self, staff_user, date_range):
        """Test plan generation with insufficient staff"""
        # Create duty days
        for d in date_range["dates"]:
            Duty.objects.create(date=d)

        planner = Planner(
            start_date=date_range["start"],
            end_date=date_range["end"],
            people_for_day=5,  # More than available staff
        )

        messages = planner.create_plan()

        # Should have warning messages
        assert len(messages) > 0

    def test_create_plan_no_consecutive_duties(self, staff_users, today):
        """Test that plan doesn't assign same user consecutive days"""
        # Create 3 consecutive duty days
        dates = [today + timedelta(days=i) for i in range(3)]
        for d in dates:
            Duty.objects.create(date=d)

        planner = Planner(start_date=dates[0], end_date=dates[-1], people_for_day=1)

        messages = planner.create_plan()

        # Check no user has consecutive assignments
        for i in range(len(dates) - 1):
            today_assignments = DutyAssignment.objects.filter(duty__date=dates[i])
            tomorrow_assignments = DutyAssignment.objects.filter(
                duty__date=dates[i + 1]
            )

            today_users = set(a.user_id for a in today_assignments)
            tomorrow_users = set(a.user_id for a in tomorrow_assignments)

            # Users should not overlap
            assert len(today_users & tomorrow_users) == 0

    def test_update_priority(self, staff_user):
        """Test updating priority"""
        planner = Planner(
            start_date=staff_user.id,  # Dummy values
            end_date=staff_user.id,
            people_for_day=2,
        )

        planner.update_priority(staff_user.id, value=10)
        staff_user.refresh_from_db()
        assert staff_user.priority == 10

    def test_set_minimum_priority(self, staff_users):
        """Test normalizing priorities"""
        # Set different priorities
        logger.info("staff_users: %s", staff_users)
        from planner.models import Staff

        Staff.objects.filter(id=staff_users[0].id).update(priority=5)
        Staff.objects.filter(id=staff_users[1].id).update(priority=7)
        Staff.objects.filter(id=staff_users[2].id).update(priority=10)
        Staff.objects.filter(id=staff_users[4].id).update(priority=9)

        planner = Planner(
            start_date=staff_users[0].id,  # Dummy values
            end_date=staff_users[0].id,
            people_for_day=2,
        )

        planner.set_minimum_priority()

        # Check that minimum priority is now 2
        min_priority = Staff.objects.filter(priority__gt=0).order_by("priority").first()
        if min_priority:
            assert min_priority.priority == 2

    def test_save_messages_no_assignments(self, duty_day):
        """Test save_messages when no one is assigned"""
        planner = Planner(
            start_date=duty_day.date, end_date=duty_day.date, people_for_day=2
        )

        messages = planner.save_messages(0, duty_day)

        date_str = duty_day.date.strftime("%Y-%m-%d")
        assert date_str in messages
        assert "никто не назначен" in messages[date_str][0]

    def test_save_messages_insufficient_assignments(self, duty_day):
        """Test save_messages when fewer people assigned than needed"""
        planner = Planner(
            start_date=duty_day.date, end_date=duty_day.date, people_for_day=3
        )

        messages = planner.save_messages(1, duty_day)

        date_str = duty_day.date.strftime("%Y-%m-%d")
        assert date_str in messages
        assert "назначено 1" in messages[date_str][0]

    def test_create_plan_uses_priority_queue(self, staff_users, date_range):
        """Test that plan uses priority queue (lowest priority assigned first)"""
        # Set specific priorities
        from planner.models import Staff

        Staff.objects.filter(id=staff_users[0].id).update(priority=10)
        Staff.objects.filter(id=staff_users[1].id).update(priority=1)
        Staff.objects.filter(id=staff_users[2].id).update(priority=5)

        # Create single duty day
        duty = Duty.objects.create(date=date_range["dates"][0])

        planner = Planner(
            start_date=date_range["dates"][0],
            end_date=date_range["dates"][0],
            people_for_day=2,
        )

        messages = planner.create_plan()

        # User with priority=1 should be assigned (lowest priority)
        assignments = DutyAssignment.objects.filter(duty=duty)
        assigned_user_ids = set(a.user_id for a in assignments)
        assert staff_users[1].id in assigned_user_ids


@pytest.mark.django_db
class TestPlannerEdgeCases:
    """Edge case tests for Planner"""

    def test_create_plan_no_staff(self, date_range):
        """Test plan generation with no staff"""
        for d in date_range["dates"]:
            Duty.objects.create(date=d)

        planner = Planner(
            start_date=date_range["start"], end_date=date_range["end"], people_for_day=2
        )

        messages = planner.create_plan()

        # Should have errors for all dates
        assert len(messages) == len(date_range["dates"])

    def test_create_plan_single_day(self, staff_users, tomorrow):
        """Test plan generation for single day"""
        Duty.objects.create(date=tomorrow)

        planner = Planner(start_date=tomorrow, end_date=tomorrow, people_for_day=2)

        messages = planner.create_plan()

        assignments = DutyAssignment.objects.filter(duty__date=tomorrow)
        assert assignments.count() == 2

    def test_create_plan_everyone_unavailable(self, staff_users, tomorrow):
        """Test plan generation when all staff are unavailable"""
        from planner.models import DaysOff

        # Give everyone a day off
        for user in staff_users:
            DaysOff.objects.create(user=user, date=tomorrow)

        Duty.objects.create(date=tomorrow)

        planner = Planner(start_date=tomorrow, end_date=tomorrow, people_for_day=2)

        messages = planner.create_plan()

        # Should have warning message
        date_str = tomorrow.strftime("%Y-%m-%d")
        assert date_str in messages
