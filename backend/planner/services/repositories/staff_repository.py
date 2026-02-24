from django.db.models import F
from django.db.models.functions import Greatest
from planner.models import Staff


class StaffRepository:

    def get_all(self):
        return Staff.objects.all()

    def get_by_id(self, staff_id):
        return Staff.objects.get(id=staff_id)

    def create(self, **kwargs):
        return Staff.objects.create(**kwargs)

    def update(self, staff_id, **kwargs):
        staff = self.get_by_id(staff_id)
        for key, value in kwargs.items():
            setattr(staff, key, value)
        staff.save()
        return staff

    def delete(self, staff_id):
        staff = self.get_by_id(staff_id)
        staff.delete()

    def update_priority_by_diff(self, user_id, diff):
        Staff.objects.filter(id=user_id).update(
            priority=Greatest(F("priority") + diff, 0)
        )

    def update_priority_by_value(self, user_id, value):
        Staff.objects.filter(id=user_id).update(priority=Greatest(value, 0))
