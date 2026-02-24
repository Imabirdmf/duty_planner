from planner.models import DaysOff


class DaysOffRepository:

    def get_all(self):
        return DaysOff.objects.all()

    def get_by_id(self, dayoff_id):
        return DaysOff.objects.get(id=dayoff_id)

    def create(self, **kwargs):
        return DaysOff.objects.create(**kwargs)

    def update(self, dayoff_id, **kwargs):
        dayoff = self.get_by_id(dayoff_id)
        for key, value in kwargs.items():
            setattr(dayoff, key, value)
        dayoff.save()
        return dayoff

    def delete(self, dayoff_id):
        dayoff = self.get_by_id(dayoff_id)
        dayoff.delete()

    def exists_for_user_in_date(self, user_id, date):
        return DaysOff.objects.filter(user_id=user_id, date=date).exists()
