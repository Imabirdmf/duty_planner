from planner.models import DutyAssignment


class DutyAssignmentRepository:
    def user_has_assignment_for_duty_id(self, user_id, duty_id):
        return DutyAssignment.objects.filter(user_id=user_id, duty_id=duty_id).exists()
