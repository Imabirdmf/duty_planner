import heapq
from random import shuffle

from django.db import transaction

from .repositories.days_off_repository import DaysOffRepository
from .repositories.duty_assignment_repository import DutyAssignmentRepository
from .repositories.duty_repository import DutyRepository
from .repositories.staff_repository import StaffRepository
from .staff_availability import StaffAvailability


class Planner:
    def __init__(self, start_date, end_date, people_for_day=2):
        self.duty_assignment_repo = DutyAssignmentRepository()
        self.staff_repo = StaffRepository()
        self.days_off_repo = DaysOffRepository()
        self.duty_repo = DutyRepository()
        self.messages = {}
        self.people_for_day = people_for_day
        self.start_date = start_date
        self.end_date = end_date

    def update_priority(self, user_id, value=None, diff=None):
        if value is not None:
            self.staff_repo.update_priority_by_value(user_id, value)
        elif diff is not None:
            self.staff_repo.update_priority_by_diff(user_id, diff)

    def set_minimum_priority(self):
        print("Set minimum priority")
        with transaction.atomic():
            min_priority = self.staff_repo.get_minimum_priority()
            if min_priority is not None:
                self.staff_repo.set_minimum_priority_for_all(min_priority)

    def save_messages(self, count, duty):
        dt = duty.date.strftime("%Y-%m-%d")
        if count == 0:
            self.messages.setdefault(
                dt, [f"На дату {dt} никто не назначен, а надо {self.people_for_day}"]
            )

        elif count < self.people_for_day:
            self.messages.setdefault(
                dt,
                [
                    f"На дату {dt} назначено {count} дежурных вместо {self.people_for_day}"
                ],
            )
        return self.messages

    def create_plan(self):
        duties_for_month = self.duty_repo.get_list_of_duties_ordered_by_date(
            self.start_date, self.end_date
        )
        print(f"duties for month: {duties_for_month}")
        staff_availability = StaffAvailability()

        with transaction.atomic():
            staff = self.staff_repo.get_all()
            users = [(user.priority, user.id) for user in staff]
            shuffle(users)
            heapq.heapify(users)
            print(self.people_for_day)
            print(f"users before generation: {users}")
            for duty in duties_for_month:

                print(f"duty day: {duty.date}")
                count = self.duty_assignment_repo.get_count_by_duty_id(duty.id)
                print(f"count for day: {count}")
                added_users = []
                while users and count < self.people_for_day:

                    user_priority, user_id = heapq.heappop(users)
                    print(f"chosen: {user_priority, user_id}")
                    if not staff_availability.is_unavailable(user_id, duty.date):
                        self.duty_assignment_repo.create(user_id=user_id, duty=duty)
                        count += 1
                        added_users.append((user_priority + 1, user_id))
                        print(f"added assignment: {user_priority, user_id}")
                    else:
                        added_users.append((user_priority, user_id))
                        print(f"not added assignment: {user_priority, user_id}")

                for user in added_users:
                    heapq.heappush(users, user)
                print(f"heap after assignment: {users}")
                self.save_messages(count, duty)

            for user_priority, user_id in users:
                self.update_priority(user_id, value=user_priority)
        print(self.messages)
        return self.messages
