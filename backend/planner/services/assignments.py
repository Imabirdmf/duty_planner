import datetime
import logging

from django.db import transaction
from django.db.models import QuerySet
from planner.models import DaysOff, Duty, DutyAssignment, Staff
from planner.services.planner import Planner
from planner.services.repositories.days_off_repository import DaysOffRepository
from planner.services.repositories.duty_assignment_repository import (
    DutyAssignmentRepository,
)
from planner.services.repositories.duty_repository import DutyRepository
from planner.services.repositories.staff_repository import StaffRepository

logger = logging.getLogger(__name__)


class ManageAssignments:
    def __init__(self):
        self.duty_repo = DutyRepository()
        self.duty_assignment_repo = DutyAssignmentRepository()
        self.staff_repo = StaffRepository()
        self.days_off_repo = DaysOffRepository()

    def create_plan(self, start_date, end_date, people_per_day) -> dict:
        plan = Planner(
            start_date,
            end_date,
            people_per_day,
            duty_repo=self.duty_repo,
            staff_repo=self.staff_repo,
            days_off_repo=self.days_off_repo,
            duty_assignment_repo=self.duty_assignment_repo,
        )
        errors = plan.create_plan()
        plan.set_minimum_priority()
        return errors

    def _resolve_date_range(
        self, start_date: datetime.date, end_date: datetime.date | None
    ) -> tuple[datetime.date, datetime.date]:
        return start_date, end_date if end_date is not None else start_date

    def get_duties_by_date(
        self, start_date: datetime.date, end_date: datetime.date | None = None
    ) -> QuerySet[Duty]:
        start_date, end_date = self._resolve_date_range(start_date, end_date)
        return self.duty_repo.get_list_of_duties(start_date, end_date)

    def create_duty_days(self, dates: list[datetime.date]) -> list[datetime.date]:
        sorted_dates = sorted(dates)
        return self.duty_repo.save_duty_days(sorted_dates)

    def get_duty_assignments(
        self, start_date: datetime.date, end_date: datetime.date | None = None
    ) -> QuerySet[DutyAssignment]:
        start_date, end_date = self._resolve_date_range(start_date, end_date)
        return self.duty_assignment_repo.get_list_of_duty_assignment(
            start_date, end_date
        )

    def get_date_range(
        self, dates: list[datetime.date]
    ) -> tuple[datetime.date, datetime.date]:
        return dates[0], dates[-1]

    def get_days_off(
        self,
        start_date: datetime.date | None = None,
        end_date: datetime.date | None = None,
    ) -> QuerySet[DaysOff]:
        if start_date and end_date:
            return self.days_off_repo.get_list_of_days_off(start_date, end_date)
        else:
            return self.days_off_repo.get_all()

    def get_all_staff(self) -> QuerySet[Staff]:
        return self.staff_repo.get_all()

    def get_all_duty_assignments(self) -> QuerySet[DutyAssignment]:
        return self.duty_assignment_repo.get_all()

    def get_all_duties(self) -> QuerySet[Duty]:
        return self.duty_repo.get_all()

    def create_assignment(
        self, duty_date: datetime.date, user_id: int
    ) -> DutyAssignment:
        with transaction.atomic():
            duty = self.duty_repo.get_first_element_by_date(duty_date)
            duty_assignment = self.duty_assignment_repo.create(
                duty=duty, user_id=user_id
            )
            self.staff_repo.update_priority(user_id, diff=1)
        return duty_assignment

    def update_assignment(
        self, duty_date: datetime.date, prev_user_id: int, new_user_id: int
    ) -> DutyAssignment:
        with transaction.atomic():
            duty = self.duty_repo.get_first_element_by_date(duty_date)
            duty_assignment = self.duty_assignment_repo.get_assignment_by_duty_and_user(
                duty.id, prev_user_id
            )
            self.duty_assignment_repo.update(duty_assignment.id, user_id=new_user_id)
            self.staff_repo.update_priority(new_user_id, diff=1)
            self.staff_repo.update_priority(prev_user_id, diff=-1)
        return duty_assignment

    def delete_assignment(self, duty_date: datetime.date, user_id: int) -> None:
        with transaction.atomic():
            duty_assignment = self.duty_assignment_repo.get_first_element_by_user(
                duty_date, user_id
            )
            self.duty_assignment_repo.delete(duty_assignment.id)

    def make_assignment(
        self, duty_date, prev_user_id: int | None, new_user_id: int | None
    ) -> None:
        if prev_user_id and new_user_id:
            self.update_assignment(duty_date, prev_user_id, new_user_id)
        elif prev_user_id is None and new_user_id:
            self.create_assignment(duty_date, user_id=new_user_id)
        elif prev_user_id and new_user_id is None:
            self.delete_assignment(duty_date, user_id=prev_user_id)
