from planner.models import Duty


class DutyRepository:

    def get_previous_duty(self, date):
        return (
            Duty.objects.filter(date__lt=date)
            .order_by("date")
            .values_list("id", flat=True)
            .last()
        )
