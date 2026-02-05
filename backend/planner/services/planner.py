import heapq

from planner.models import DaysOff, Duty, DutyAssignment, Staff


def create_plan(people_for_day=2):
    duties = Duty.objects.all().order_by("date")

    for duty in duties:
        users = [(user.priority, user.id) for user in Staff.objects.all()] # вытащить один раз вне цикла. после каждого проставления возвращать пользователей в хип
        heapq.heapify(users)
        print(users)
        count = 0
        print("duty", duty)
        while count < people_for_day:
            if len(users) == 0:
                break

            user = heapq.heappop(users)
            print("user", user)
            if not get_days_off(user[1], duty.date) and not user_has_previous_duty(user[1], duty.date):
                create_duty_assignment(user[1], duty)
                update_priority(user_id=user[1])
                count += 1

        if count == 0:
            print(f'На дату {duty.date} никто не назначен, а надо {people_for_day}')

        elif count < people_for_day:
            print(f'На дату {duty.date} назначено {count} дежурных вместо {people_for_day}')


def get_days_off(user_id, date):
    days_off = DaysOff.objects.filter(user_id=user_id, date=date)
    print("days_off", days_off)
    return True if days_off else False


def create_duty_assignment(user_id, duty):
    duty_assignment, created = DutyAssignment.objects.update_or_create(
        user_id=user_id,
        duty=duty,
    )
    duty_assignment.save()
    print("duty_assignment created")


def update_priority(user_id):
    user = Staff.objects.get(id=user_id)
    user.priority += 1
    user.save()
    print("user.priority", user.priority)


def user_has_previous_duty(user_id, date):
    duties = Duty.objects.filter(date__lt = date).order_by("date")
    if len(duties) == 0:
        print("duties", False)
        return False
    prev_duty_id = duties.last().id
    user_has_previous_duty = DutyAssignment.objects.filter(user_id=user_id, duty_id=prev_duty_id).exists()
    print("user_has_previous_duty", user_has_previous_duty)
    print("duties", duties)
    return user_has_previous_duty

