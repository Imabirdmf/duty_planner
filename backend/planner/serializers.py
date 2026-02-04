from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.utils import timezone

from .models import Staff, DaysOff


class StaffSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Staff
        fields = ("id", "email", "last_name", "first_name", "full_name")


class DaysOffSerializer(serializers.ModelSerializer):
    def validate_date(self, value):
        if not self.instance and value < timezone.localdate():
            raise serializers.ValidationError(
                "Нельзя добавить выходной в прошедшую дату"
            )
        return value

    class Meta:
        model = DaysOff
        fields = ("id", "date", "user")
        validators = [
            UniqueTogetherValidator(queryset=DaysOff.objects.all(),
                                    fields=["user", "date"],
                                    message="У этого сотрудника уже есть выходной на указанную дату")
        ]


