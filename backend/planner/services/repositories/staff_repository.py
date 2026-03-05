import datetime
import logging

from django.db.models import F, Min, Count, Q
from django.db.models.functions import Greatest
from planner.models import Staff
from planner.services.repositories.base_repository import BaseRepository

logger = logging.getLogger(__name__)


class StaffRepository(BaseRepository[Staff]):
    model = Staff
    default_ordering = "email"

    def update_priority(self, user_id: int, value=None, diff=None) -> None:
        if value is not None:
            Staff.objects.filter(id=user_id).update(priority=Greatest(value, 0))
        elif diff is not None:
            Staff.objects.filter(id=user_id).update(
                priority=Greatest(F("priority") + diff, 0)
            )

    def get_minimum_priority(self) -> int:
        users = Staff.objects.filter(priority__gt=0)
        min_priority = users.aggregate(min_priority=Min("priority"))["min_priority"]
        return min_priority

    def set_minimum_priority_for_all(self, min_priority: int) -> None:
        users = Staff.objects.filter(priority__gt=0)
        logger.info(
            "пользователи после фильтрации: %s", [(u.priority, u.id) for u in users]
        )
        logger.info("min_priority: %s", min_priority)
        users.update(priority=F("priority") - min_priority)
        logger.info(
            "пользователи после апдейта: %s", [(u.priority, u.id) for u in users]
        )

    def get_duty_stats(self, start_date:datetime.date, end_date: datetime.date):
        return Staff.objects.annotate(
            duty_count=Count(
                "dutyassignment",
                filter=Q(dutyassignment__duty__date__gte=start_date,
                         dutyassignment__duty__date__lte=end_date)
            )
        ).order_by("-duty_count")