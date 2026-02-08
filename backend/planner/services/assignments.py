from datetime import datetime

from planner.models import DutyAssignment, Duty, Staff
from .duty_calendar import get_duty_days
from .planner import create_duty_assignment, update_priority
import calendar

def get_assignments(month_start):
    month_end = month_start.replace(
        day=calendar.monthrange(month_start.year, month_start.month)[1]
    )

    duty_assignments = (DutyAssignment.objects.filter(duty__date__gte=month_start, duty__date__lte=month_end)
                        .select_related('user'))

    return duty_assignments


def make_assignment(prev_user, duty_date, new_user=None):
    exists_assignment = get_assignments(duty_date).filter(user__id=prev_user)
    duty = exists_assignment.get().duty
    exists_assignment.update(user_id=new_user, duty=duty)
    update_priority(prev_user, -1)
    update_priority(new_user, 1)

    new_assignment = get_assignments(duty_date).filter(user__id=new_user).get()
    return new_assignment
