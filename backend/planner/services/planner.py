import heapq
import logging
from random import shuffle

from django.db import transaction

from .repositories.days_off_repository import DaysOffRepository
from .repositories.duty_assignment_repository import DutyAssignmentRepository
from .repositories.duty_repository import DutyRepository
from .repositories.staff_repository import StaffRepository
from .staff_availability import StaffAvailability

logger = logging.getLogger(__name__)


class Planner:
    def __init__(
        self,
        start_date,
        end_date,
        people_for_day=2,
        duty_repo=None,
        staff_repo=None,
        days_off_repo=None,
        duty_assignment_repo=None,
    ):
        self.duty_repo = duty_repo or DutyRepository()
        self.staff_repo = staff_repo or StaffRepository()
        self.days_off_repo = days_off_repo or DaysOffRepository()
        self.duty_assignment_repo = duty_assignment_repo or DutyAssignmentRepository()
        self.messages = {}
        self.people_for_day: int = people_for_day
        self.start_date = start_date
        self.end_date = end_date

    def update_priority(self, user_id, value=None, diff=None):
        self.staff_repo.update_priority(user_id, value, diff)

    def set_minimum_priority(self):
        logger.info("Set minimum priority")
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
        duties_for_month = self.duty_repo.get_list_of_duties(
            self.start_date, self.end_date, ordered=True
        )
        logger.info("duties for month: %s", duties_for_month)
        staff_availability = StaffAvailability()

        with transaction.atomic():  # убрать
            staff = self.staff_repo.get_all()
            users = [(user.priority, user.id) for user in staff]
            shuffle(users)
            heapq.heapify(users)
            logger.info(self.people_for_day)
            logger.info("users before generation: %s", users)
            for duty in duties_for_month:

                logger.info("duty day: %s", duty.date)
                count = self.duty_assignment_repo.get_count_by_duty_id(duty.id)
                logger.info("count for day: %s", count)
                added_users = []
                while users and count < self.people_for_day:

                    user_priority, user_id = heapq.heappop(users)
                    logger.info("chosen: %s", (user_priority, user_id))
                    if not staff_availability.is_unavailable(user_id, duty.date):
                        self.duty_assignment_repo.create(user_id=user_id, duty=duty)
                        count += 1
                        added_users.append((user_priority + 1, user_id))
                        logger.info("added assignment: %s", (user_priority, user_id))
                    else:
                        added_users.append((user_priority, user_id))
                        logger.info(
                            "not added assignment: %s", (user_priority, user_id)
                        )

                for user in added_users:
                    heapq.heappush(users, user)
                logger.info("heap after assignment: %s", users)
                self.save_messages(count, duty)

            for user_priority, user_id in users:
                self.update_priority(user_id, value=user_priority)
        return self.messages
