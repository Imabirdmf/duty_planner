from datetime import date

from planner.validators import validate_date_not_past
from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator

from .models import DaysOff, DutyAssignment, Staff, Duty


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

class DutyAssignmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = DutyAssignment
        fields = ("id", "duty", "user")


class DutyAssignmentQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


class DutyAssignmentGenerateSerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.DateField())
    people_per_day = serializers.IntegerField(max_value=10)


class DutyAssignmentChangeSerializer(serializers.Serializer):
    user_id_prev = serializers.IntegerField(allow_null=True)
    user_id_new = serializers.IntegerField(allow_null=True)
    date = serializers.DateField()


class DutyWithAssignmentsSerializer(serializers.ModelSerializer):
    users = serializers.SerializerMethodField()

    class Meta:
        model = Duty
        fields = ("id", "date", "users")

    def get_users(self, obj):
        assignments = obj.dutyassignment_set.all()
        users = [a.user for a in assignments]
        return StaffSerializer(users, many=True).data


# class CalendarMonthQuerySerializer(serializers.Serializer):
#     month = serializers.CharField()
#
#     def validate(self, attrs):
#         value = attrs["month"]
#         year_str, month_str = value.split("-")
#         attrs["month"] = date(int(year_str), int(month_str), 1)
#
#         return attrs
#
#
# class CalendarResponseSerializer(serializers.Serializer):
#     month = serializers.CharField()
#     dates = serializers.ListField(child=serializers.DateField())

# class DutySerializer(serializers.ModelSerializer):
#     date = serializers.DateField(validators=[validate_date_not_past])
#
#     class Meta:
#         model = Duty
#         fields = ("id", "date")