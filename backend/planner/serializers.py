from datetime import date

from planner.validators import validate_date_not_past
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import DaysOff, Duty, DutyAssignment, Staff


class StaffSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()

    class Meta:
        model = Staff
        fields = ("id", "email", "last_name", "first_name", "full_name")


class DaysOffSerializer(serializers.ModelSerializer):
    date = serializers.DateField(validators=[validate_date_not_past])

    class Meta:
        model = DaysOff
        fields = ("id", "date", "user")
        validators = [
            UniqueTogetherValidator(
                queryset=DaysOff.objects.all(),
                fields=["user", "date"],
                message="У этого сотрудника уже есть выходной на указанную дату",
            )
        ]


class DutySerializer(serializers.ModelSerializer):
    date = serializers.DateField(validators=[validate_date_not_past])

    class Meta:
        model = Duty
        fields = ("id", "date")


class DutyAssignmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = DutyAssignment
        fields = ("id", "date", "user")


class CalendarMonthQuerySerializer(serializers.Serializer):
    month = serializers.CharField()

    def validate(self, attrs):
        value = attrs["month"]
        year_str, month_str = value.split("-")
        attrs["month"] = date(int(year_str), int(month_str), 1)

        return attrs


class CalendarResponseSerializer(serializers.Serializer):
    month = serializers.CharField()
    dates = serializers.ListField(child=serializers.DateField())
