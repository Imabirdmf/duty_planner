import calendar

from django.db import transaction
from planner.models import DutyAssignment

from .planner import update_priority


def get_assignments(date_start, date_end=None):
    if date_end is None:
        date_end = date_start
    duty_assignments = DutyAssignment.objects.filter(
        duty__date__gte=date_start, duty__date__lte=date_end
    ).order_by('duty__date').select_related("user", "duty")

    return duty_assignments


def make_assignment(prev_user, duty_date, new_user=None):
    exists_assignment = get_assignments(duty_date).filter(user__id=prev_user)
    with transaction.atomic():
        exists_assignment.update(user_id=new_user)
        update_priority(prev_user, -1)
        if new_user:
            update_priority(new_user, 1)
        new_assignment = get_assignments(duty_date).filter(user__id=new_user).get()
        return new_assignment


def assignments_response(duty_assignments):
    sp = list(duty_assignments)
    result = []
    last = None
    for el in sp:
        if last is None:
            last = {'date': el.duty.date, 'users': [el.user]}
        elif last['date'] == el.duty.date:
            last['users'].append(el.user)
        else:
            result.append(last)
            last = {'date': el.duty.date, 'users': [el.user]}
    result.append(last)
    return result