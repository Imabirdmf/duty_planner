from django.db.models import F, Min
from django.db.models.functions import Greatest
from planner.models import Staff
from planner.services.repositories.base_repository import BaseRepository


class StaffRepository(BaseRepository[Staff]):
    model = Staff

    def update_priority(self, user_id, value=None, diff=None):
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

    def set_minimum_priority_for_all(self, min_priority: int):
        users = Staff.objects.filter(priority__gt=0)
        users.update(priority=F("priority") - min_priority)
