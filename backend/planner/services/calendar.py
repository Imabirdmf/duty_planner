import calendar

from planner.models import Duty


def get_duty_days(month_start):
    month_end = month_start.replace(
        day=calendar.monthrange(month_start.year, month_start.month)[1]
    )

    data = Duty.objects.filter(date__gte=month_start, date__lte=month_end)

    return data


def save_duty_days(month_start, dates):
    Duty.objects.bulk_update_or_create(
        [Duty(date=duty_date) for duty_date in dates],
        update_fields=["date"],
        match_field=["date"],
    )
    data = get_duty_days(month_start)
    return data
