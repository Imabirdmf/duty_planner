from django.db import transaction
from planner.services.repositories.duty_assignment_repository import (
    DutyAssignmentRepository,
)
from planner.services.repositories.duty_repository import DutyRepository
from planner.services.repositories.staff_repository import StaffRepository


class ManageAssignments:
    def __init__(self):
        self.duty_repo = DutyRepository()
        self.duty_assignment_repo = DutyAssignmentRepository()
        self.staff_repo = StaffRepository()

    def get_duties(self, start_date, end_date=None):
        if end_date is None:
            end_date = start_date
        return self.duty_repo.get_list_of_duties(start_date, end_date)

    def create_duty_days(self, dates):
        sorted_dates = sorted(dates)
        return self.duty_repo.save_duty_days(sorted_dates)

    def get_duty_assignments(self, start_date, end_date=None):
        if end_date is None:
            end_date = start_date
        return self.duty_assignment_repo.get_list_of_duty_assignment(
            start_date, end_date
        )

    def make_assignment(self, duty_date, prev_user=None, new_user=None):
        duty = self.duty_repo.get_first_element_for_date(duty_date)
        print("duty", duty, duty.id)
        with transaction.atomic():
            if prev_user is None and new_user:
                duty_assignment = self.duty_assignment_repo.create(
                    duty=duty, user_id=new_user
                )
                self.staff_repo.update_priority_for_one_by_diff(new_user, diff=1)
            elif prev_user and new_user:
                duty_assignment = (
                    self.duty_assignment_repo.get_assignment_by_duty_and_user(
                        duty.id, prev_user.id
                    )
                )

                self.duty_assignment_repo.update(duty_assignment.id, user_id=new_user)
                self.staff_repo.update_priority_for_one_by_diff(new_user, diff=1)
                self.staff_repo.update_priority_for_one_by_diff(prev_user, diff=-1)
            elif prev_user and new_user is None:
                print("удаляю")
                print(duty, prev_user)
                self.delete_assignment(duty.id, prev_user)
                return self.duty_assignment_repo.get_first_element_by_date(duty_date)

            return duty_assignment

    def delete_assignment(self, duty_id, user_id):
        self.duty_assignment_repo.delete(duty_id, user_id)
