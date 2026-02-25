from django.db.models import F, Min
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

    def update_priority_for_one_by_diff(self, user_id, diff):
        Staff.objects.filter(id=user_id).update(
            priority=Greatest(F("priority") + diff, 0)
        )

    def update_priority_by_value(self, user_id, value):
        Staff.objects.filter(id=user_id).update(priority=Greatest(value, 0))

    def get_minimum_priority(self) -> int:
        users = Staff.objects.filter(priority__gt=0)
        print(f"Users: {users}")
        print(f"after filtration: {Staff.objects.filter(priority__gt=0)}")
        min_priority = users.aggregate(min_priority=Min("priority"))["min_priority"]
        print(f"min_priority: {min_priority}")
        return min_priority

    def set_minimum_priority_for_all(self, min_priority: int):
        users = Staff.objects.filter(priority__gt=0)
        users.update(priority=F("priority") - min_priority)
