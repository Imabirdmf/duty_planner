from planner.validators import validate_date_not_past
from rest_framework import serializers

from .models import DaysOff, Duty, DutyAssignment, Staff
from .services.repositories.days_off_repository import DaysOffRepository
from .services.repositories.duty_assignment_repository import DutyAssignmentRepository


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

    def validate(self, data):
        repo = DaysOffRepository()
        if repo.exists_for_user_in_date(data["user"].id, data["date"]):
            raise serializers.ValidationError(
                "У этого сотрудника уже есть выходной на указанную дату"
            )
        return data


class DutyAssignmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = DutyAssignment
        fields = ("id", "duty", "user")


class DatesQuerySerializer(serializers.Serializer):
    start_date = serializers.DateField(required=True)
    end_date = serializers.DateField(required=True)


class DutyAssignmentGenerateSerializer(serializers.Serializer):
    dates = serializers.ListField(child=serializers.DateField(), allow_empty=False)
    people_per_day = serializers.IntegerField(max_value=10, min_value=1)


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
        repo = DutyAssignmentRepository()
        users = repo.get_users_for_duty(obj.id)
        return StaffSerializer(users, many=True).data
