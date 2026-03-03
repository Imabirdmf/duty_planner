from django.db.models import QuerySet
from planner.models import DaysOff
from planner.services.repositories.base_repository import BaseRepository


class DaysOffRepository(BaseRepository[DaysOff]):
    model = DaysOff

    def get_all(self):
        return self.model.objects.all().order_by("date")

    def exists_for_user_in_date(self, user_id, date) -> bool:
        return DaysOff.objects.filter(user_id=user_id, date=date).exists()

    def get_list_of_days_off(self, start_date, end_date) -> QuerySet[DaysOff]:
        return DaysOff.objects.filter(
            date__gte=start_date, date__lte=end_date
        ).order_by("date")
