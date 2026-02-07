from bulk_update_or_create import BulkUpdateOrCreateQuerySet
from django.db import models


class Staff(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    priority = models.IntegerField(default=0)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name


class DaysOff(models.Model):
    user = models.ForeignKey(Staff, on_delete=models.CASCADE)
    date = models.DateField(db_index=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="unique_day_off")
        ]

    def __str__(self):
        return f"{self.date} - userid: {self.user.id}"


class Duty(models.Model):
    date = models.DateField(db_index=True, unique=True)

    objects = BulkUpdateOrCreateQuerySet.as_manager()

    def __str__(self):
        return str(self.date)


class DutyAssignment(models.Model):
    user = models.ForeignKey(Staff, on_delete=models.CASCADE)
    duty = models.ForeignKey(Duty, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.duty.date} - userid: {self.user.id}"
