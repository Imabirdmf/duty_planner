import datetime

from django.db.models import QuerySet
from planner.models import Duty
from planner.services.repositories.base_repository import BaseRepository


class DutyRepository(BaseRepository[Duty]):
    model = Duty

    def get_previous_duty(self, date) -> Duty:
        return (
            Duty.objects.filter(date__lt=date)
            .order_by("date")
            .values_list("id", flat=True)
            .last()
        )

    def get_list_of_duties(
        self, start_date: datetime.date, end_date: datetime.date
    ) -> QuerySet[Duty]:
        return Duty.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).prefetch_related("dutyassignment_set__user")

    def get_first_element_by_date(self, duty_date) -> Duty:
        return Duty.objects.filter(date=duty_date).first()

    def get_list_of_duties_ordered_by_date(
        self, date_start, date_end
    ) -> QuerySet[Duty]:
        return Duty.objects.filter(date__gte=date_start, date__lte=date_end).order_by(
            "date"
        )

    def save_duty_days(self, dates: list[datetime.date,]) -> list[datetime.date,]:
        Duty.objects.bulk_update_or_create(
            [Duty(date=duty_date) for duty_date in dates],
            update_fields=["date"],
            match_field=["date"],
        )
        data = self.get_list_of_duties_ordered_by_date(
            date_start=dates[0], date_end=dates[-1]
        )
        return [d.date for d in data]
