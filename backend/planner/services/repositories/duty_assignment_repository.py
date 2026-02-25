from planner.models import DutyAssignment


class DutyAssignmentRepository:

    def get_all(self):
        return DutyAssignment.objects.all()

    def get_by_id(self, duty_assignment_id):
        print("пытаюсь получить по id", duty_assignment_id)
        return DutyAssignment.objects.get(id=duty_assignment_id)

    def user_has_assignment_for_duty_id(self, user_id, duty_id):
        return DutyAssignment.objects.filter(user_id=user_id, duty_id=duty_id).exists()

    def get_list_of_duty_assignment(self, start_date, date_end):
        print(
            "get_list_of_duty_assignment",
            DutyAssignment.objects.filter(
                duty__date__gte=start_date, duty__date__lte=date_end
            ).select_related("duty", "user"),
        )
        return DutyAssignment.objects.filter(
            duty__date__gte=start_date, duty__date__lte=date_end
        ).select_related("duty", "user")

    def get_assignment_by_duty_and_user(self, duty_id, user_id):
        return DutyAssignment.objects.filter(user_id=user_id, duty_id=duty_id)

    def get_first_element_by_user(self, date, user_id):
        return (
            self.get_list_of_duty_assignment(date, date)
            .filter(user__id=user_id)
            .first()
        )

    def get_first_element_by_date(self, date):
        return self.get_list_of_duty_assignment(date, date).first()

    def get_count_by_duty_id(self, duty_id):
        return DutyAssignment.objects.filter(duty__id=duty_id).count()

    def create(self, **kwargs):
        return DutyAssignment.objects.create(**kwargs)

    def update(self, id, **kwargs):
        duty_assignment = self.get_by_id(id)
        for key, value in kwargs.items():
            setattr(duty_assignment, key, value)
        duty_assignment.save()
        return duty_assignment

    def delete(self, duty_id, user_id):
        print("пытаюсь удалить")
        self.get_assignment_by_duty_and_user(duty_id, user_id).delete()
