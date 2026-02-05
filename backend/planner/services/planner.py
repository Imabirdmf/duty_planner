import heapq

from planner.models import DaysOff, Duty, DutyAssignment, Staff


def create_plan(people_for_day=2):
    users = [(user.priority, user.id) for user in Staff.objects.all()]
    print(users)
    duties = Duty.objects.all()

    for duty in duties:
        count = 0
        print("duty", duty)
        while count < people_for_day:
            user = heapq.heappop(users)
            print("user", user)
            if not get_days_off(user[1], duty.date):
                create_duty_assignment(user[1], duty)
                update_priority(user_id=user[1])
                count += 1
            else:
                continue


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
    pass
