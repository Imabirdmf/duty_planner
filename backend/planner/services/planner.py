import heapq

from planner.models import DaysOff, Duty, DutyAssignment, Staff


def create_plan(people_for_day=2):
    messages = {}
    duties = Duty.objects.all().order_by("date")
    staff = Staff.objects.all()

    for duty in duties:
        users = [(user.priority, user.id) for user in staff]
        heapq.heapify(users)
        print("очередь", users)
        count = 0
        print("duty", duty)
        while count < people_for_day:
            if len(users) == 0:
                break

            user = heapq.heappop(users)
            print("user", user)
            if not get_days_off(user[1], duty.date) and not user_has_previous_duty(
                user[1], duty.date
            ):
                create_duty_assignment(user[1], duty)
                update_priority(user_id=user[1])
                count += 1

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

        return "Дежурные назначены", messages


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


def update_priority(user_id, value=1):
    user = Staff.objects.get(id=user_id)
    user.priority += value
    user.save()
    print("user.priority", user.priority)


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
