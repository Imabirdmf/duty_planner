import heapq
from random import shuffle

from django.db.models import F, Min
from planner.models import DaysOff, Duty, DutyAssignment, Staff

from .duty_calendar import get_duty_days


def create_plan(date_start, date_end, people_for_day=2):
    messages = {}
    duties = get_duty_days(date_start, date_end).order_by("date")
    duty_assignments = DutyAssignment.objects.filter(
        duty__date__gte=date_start, duty__date__lte=date_end
    )
    staff = Staff.objects.all()
    users = [(user.priority, user.id) for user in staff]
    shuffle(users)
    heapq.heapify(users)

    for duty in duties:

        count = duty_assignments.filter(duty__id=duty.id).count()
        added_users = []
        while count < people_for_day:
            if len(users) == 0:
                break

            user_priority, user_id = heapq.heappop(users)
            if not user_is_unavailable(user_id, duty.date):
                create_duty_assignment(user_id, duty)
                count += 1
                added_users.append((user_priority + 1, user_id))
            else:
                added_users.append((user_priority, user_id))

        if len(added_users) != 0:
            for user in added_users:
                heapq.heappush(users, user)

        save_messages(messages, count, duty, people_for_day)

    for user_priority, user_id in users:
        update_priority(user_priority, value=user_id)

    return messages


def user_is_unavailable(user_id, date):
    return any((get_days_off(user_id, date), user_has_previous_duty(user_id, date)))


def get_days_off(user_id, date):
    days_off = DaysOff.objects.filter(user_id=user_id, date=date).exists()
    return days_off


def create_duty_assignment(user_id, duty):
    duty_assignment, _ = DutyAssignment.objects.update_or_create(
        user_id=user_id,
        duty=duty,
    )
    duty_assignment.save()


def update_priority(user_id, value=None, diff=None):
    if value is not None:
        Staff.objects.filter(id=user_id).update(priority=value)
    elif diff is not None:
        Staff.objects.filter(id=user_id).update(priority=F("priority") + diff)


def user_has_previous_duty(user_id, date):
    duties = Duty.objects.filter(date__lt=date).order_by("date")
    if len(duties) == 0:
        return False
    prev_duty_id = duties.last().id
    user_previous_duty = DutyAssignment.objects.filter(
        user_id=user_id, duty_id=prev_duty_id
    ).exists()
    return user_previous_duty


def set_minimum_priority():
    users = Staff.objects.filter(priority__gt=0)
    min_priority = users.aggregate(min_priority=Min("priority"))["min_priority"]

    if min_priority is not None:
        users.update(priority=F("priority") - min_priority)


def save_messages(messages, count, duty, people_for_day):
    dt = duty.date.strftime("%Y-%m-%d")
    if count == 0:
        messages.setdefault(
            dt, [f"На дату {dt} никто не назначен, а надо {people_for_day}"]
        )

    elif count < people_for_day:
        messages.setdefault(
            dt, [f"На дату {dt} назначено {count} дежурных вместо {people_for_day}"]
        )
    return messages
