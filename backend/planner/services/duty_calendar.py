from planner.models import Duty


def get_duty_days(date_start, date_end):
    data = Duty.objects.filter(date__gte=date_start, date__lte=date_end).order_by(
        "date"
    )
    return data


def save_duty_days(dates):
    dates_sorted = sorted(dates)
    Duty.objects.bulk_update_or_create(
        [Duty(date=duty_date) for duty_date in dates_sorted],
        update_fields=["date"],
        match_field=["date"],
    )
    data = get_duty_days(date_start=dates_sorted[0], date_end=dates_sorted[-1])
    return data
