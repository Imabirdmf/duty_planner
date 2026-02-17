import heapq
from random import shuffle

from django.db.models import F
from planner.models import DaysOff, Duty, DutyAssignment, Staff

from .duty_calendar import get_duty_days


def create_plan(date_start, date_end, people_for_day=2):
    messages = {}
    print("Иду за дьюти дейс")
    duties = get_duty_days(date_start, date_end).order_by("date")
    duty_assignments = DutyAssignment.objects.filter(
        duty__date__gte=date_start, duty__date__lte=date_end
    )
    print("duties", duties)
    print("duty_assignments", duty_assignments)
    print("Иду за пользователями")
    staff = Staff.objects.all()
    users = [(user.priority, user.id) for user in staff]
    shuffle(users)
    heapq.heapify(users)
    print("users", users)
    for duty in duties:

        count = duty_assignments.filter(duty__id=duty.id).count()
        print("count", count)
        print("очередь", users)
        print("duty", duty)
        added_users = []
        while count < people_for_day:
            if len(users) == 0:
                break

            user = heapq.heappop(users)
            print("user", user)
            if not get_days_off(user[1], duty.date) and not user_has_previous_duty(
                user[1], duty.date
            ):
                create_duty_assignment(user[1], duty)
                count += 1
                added_users.append((user[0] + 1, user[1]))
            else:
                added_users.append(user)
                print("added_users", added_users)
            print(f"finish for {duty}")

        if len(added_users) != 0:
            for u in added_users:
                heapq.heappush(users, (u[0], u[1]))
            print("Очередь после возвращения", users)

        dt = duty.date.strftime("%Y-%m-%d")
        messages[dt] = messages.get(dt, [])
        if count == 0:
            messages[dt].append(
                f"На дату {dt} никто не назначен, а надо {people_for_day}"
            )

        elif count < people_for_day:
            messages[dt].append(
                f"На дату {dt} назначено {count} дежурных вместо {people_for_day}"
            )

    for u in users:
        update_priority(u[1], u[0])

    return messages


def get_days_off(user_id, date):
    days_off = DaysOff.objects.filter(user_id=user_id, date=date).exists()
    print("days_off", days_off)
    return days_off


def create_duty_assignment(user_id, duty):
    duty_assignment, _ = DutyAssignment.objects.update_or_create(
        user_id=user_id,
        duty=duty,
    )
    duty_assignment.save()
    print("duty_assignment created")


def update_priority(user_id, value=None, diff=None):
    if value:
        Staff.objects.filter(id=user_id).update(priority=value)
    elif diff:
        Staff.objects.filter(id=user_id).update(priority=F("priority") + diff)


def user_has_previous_duty(user_id, date):
    duties = Duty.objects.filter(date__lt=date).order_by("date")
    if len(duties) == 0:
        print("duties нет")
        return False
    prev_duty_id = duties.last().id
    user_previous_duty = DutyAssignment.objects.filter(
        user_id=user_id, duty_id=prev_duty_id
    ).exists()
    print("user_has_previous_duty", user_previous_duty)
    print("duties", duties)
    return user_previous_duty


def set_minimum_priority():
    users = Staff.objects.filter(priority__gt=0)
    print("priority", users)
    if len(users) > 0:
        min_priority = min(u.priority for u in users)
        print(min_priority)
        for u in users:
            update_priority(user_id=u.id, diff=-min_priority)
