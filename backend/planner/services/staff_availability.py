from planner.services.repositories.days_off_repository import DaysOffRepository
from planner.services.repositories.duty_assignment_repository import (
    DutyAssignmentRepository,
)
from planner.services.repositories.duty_repository import DutyRepository


class StaffAvailability:
    def __init__(self):
        self.days_off_repo = DaysOffRepository()
        self.duty_repo = DutyRepository()
        self.duty_assignment_repo = DutyAssignmentRepository()

    def is_unavailable(self, user_id, date):
        return self.has_days_off(user_id, date) or self.has_previous_duty(user_id, date)

    def has_days_off(self, user_id, date):
        return self.days_off_repo.exists_for_user_in_date(user_id, date)

    def has_previous_duty(self, user_id, date):
        duty_id = self.duty_repo.get_previous_duty(date)
        if duty_id is None:
            return False
        return self.duty_assignment_repo.user_has_assignment_for_duty_id(
            user_id, duty_id
        )
