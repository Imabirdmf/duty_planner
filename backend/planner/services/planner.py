import heapq
from planner.models import Staff, DaysOff, Duty, DutyAssignment


def create_plan(people_for_day=2):
    users = [(user.priority, user.id) for user in Staff.objects.all()]
    print(users)
    duties = Duty.objects.all()
    count = 0

    while count < people_for_day:
        for duty in duties:
            print('duty', duty)
            user = heapq.heappop(users)
            print('user', user)
            if not get_days_off(user[1], duty.date):
                create_duty_assignment(user[1], duty)
                update_priority(userId=user[1])
                count += 1
            else:
                continue

def get_days_off(userId, date):
    days_off = DaysOff.objects.filter(user_id=userId, date=date)
    print('days_off', days_off)
    return True if days_off else False

def create_duty_assignment(userId, duty):
    duty_assignment, created = DutyAssignment.objects.update_or_create(
        user_id=userId,
        duty=duty,
    )
    duty_assignment.save()
    print('duty_assignment created')

def update_priority(userId):
    user = Staff.objects.get(id=userId)
    user.priority += 1
    print(user.priority)
    user.save()

def user_has_previous_duty(userId, date):
    pass