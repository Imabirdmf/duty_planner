import datetime
import logging

from planner.models import Duty
from planner.services.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class DutyRepository(BaseRepository[Duty]):
    model = Duty

    def get_previous_duty(self, date: datetime.date) -> int | None:
        return (
            Duty.objects.filter(date__lt=date)
            .order_by("date")
            .values_list("id", flat=True)
            .last()
        )

    def get_first_element_by_date(self, duty_date: datetime.date) -> Duty | None:
        return Duty.objects.filter(date=duty_date).first()

    def get_list_of_duties(
        self, start_date: datetime.date, end_date: datetime.date, ordered: bool = False
    ):
        qs = Duty.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).prefetch_related("dutyassignment_set__user")

        return qs.order_by("date") if ordered else qs

    def save_duty_days(self, dates: list[datetime.date,]) -> list[datetime.date]:
        Duty.objects.bulk_update_or_create(
            [Duty(date=duty_date) for duty_date in dates],
            update_fields=["date"],
            match_field=["date"],
        )
        data = self.get_list_of_duties(
            start_date=dates[0], end_date=dates[-1], ordered=True
        )
        return [d.date for d in data]

    def bulk_delete_by_id(self, ids: list[int]):
        _, deleted_count = Duty.objects.filter(id__in=ids).delete()
        logger.info("to delete", deleted_count)
        return deleted_count.get("planner.Duty", None)
