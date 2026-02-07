import calendar

from planner.models import Duty


def get_duty_days(month_start):
    month_end = month_start.replace(
        day=calendar.monthrange(month_start.year, month_start.month)[1]
    )

    data = Duty.objects.filter(date__gte=month_start, date__lte=month_end)

    return data


# def save_duty_days(month, dates):
#     dt = datetime.strptime(month, '%Y-%m')
#     start_day = dt.replace(day=1)
#     end_day = dt.replace(day=calendar.monthrange(dt.year, dt.month)[1])
#
#     data, created = Duty.objects.update_or_create(
#
#     )
