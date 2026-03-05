import datetime

from django.db.models import Count, QuerySet
from django.db.models.functions import TruncMonth
from planner.models import DutyAssignment, Staff
from planner.services.repositories.base_repository import BaseRepository


class DutyAssignmentRepository(BaseRepository[DutyAssignment]):
    model = DutyAssignment

    def user_has_assignment_for_duty_id(self, user_id: int, duty_id: int) -> bool:
        return DutyAssignment.objects.filter(user_id=user_id, duty_id=duty_id).exists()

    def get_list_of_duty_assignment(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> QuerySet[DutyAssignment]:
        return DutyAssignment.objects.filter(
            duty__date__gte=start_date, duty__date__lte=end_date
        ).select_related("duty", "user")

    def get_assignment_by_duty_and_user(
        self, duty_id: int, user_id: int
    ) -> DutyAssignment | None:
        return DutyAssignment.objects.filter(user_id=user_id, duty_id=duty_id).first()

    def get_first_element_by_user(
        self, date: datetime.date, user_id: int
    ) -> DutyAssignment | None:
        return (
            self.get_list_of_duty_assignment(date, date)
            .filter(user__id=user_id)
            .first()
        )

    def get_count_by_duty_id(self, duty_id: int) -> int:
        return DutyAssignment.objects.filter(duty__id=duty_id).count()

    def get_users_for_duty(self, duty_id: int) -> list[Staff]:
        assignments = DutyAssignment.objects.filter(duty_id=duty_id).select_related(
            "user"
        )
        return [a.user for a in assignments]

    def get_duty_stats(self, start_date: datetime.date, end_date: datetime.date):
        return (
            DutyAssignment.objects.filter(
                duty__date__gte=start_date, duty__date__lte=end_date
            )
            .annotate(month=TruncMonth("duty__date"))
            .values("user_id", "user__last_name", "month")
            .annotate(duty_count=Count("id"))
            .order_by("user_id", "month")
        )
