import calendar
from os.path import exists

from django.db import transaction
from planner.models import DutyAssignment, Duty

from .planner import update_priority


def get_assignments(date_start, date_end=None):
    if date_end is None:
        date_end = date_start
    duty_assignments = Duty.objects.filter(date__gte=date_start, date__lte=date_end).prefetch_related("dutyassignment_set__user")
    return duty_assignments

def get_duty_assignments(date_start, date_end=None):
    if date_end is None:
        date_end = date_start
    return DutyAssignment.objects.filter(duty__date__gte=date_start,duty__date__lte=date_end).select_related('duty', 'user')

def make_assignment(duty_date, prev_user=None, new_user=None):
    duty = Duty.objects.filter(date=duty_date).first()
    print(duty)
    with transaction.atomic():
        if prev_user is None and new_user:
            assignment = DutyAssignment.objects.create(duty=duty, user_id=new_user)
            update_priority(new_user, None, diff=1)
        elif prev_user and new_user:
            assignment = get_duty_assignments(duty_date).filter(user__id=prev_user).first()
            assignment.user_id = new_user
            assignment.save()
            update_priority(new_user, None, diff=1)
            update_priority(prev_user, value=None, diff=-1)
        elif prev_user and new_user is None:
            delete_assignment(duty_date, prev_user)
        return get_assignments(duty_date).first()

def delete_assignment(duty_date, user):
    get_duty_assignments(duty_date).filter(user__id=user).delete()
