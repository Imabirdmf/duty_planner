import logging

from django.db import transaction
from django.db.models import QuerySet
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    DatesQuerySerializer,
    DaysOffSerializer,
    DutyAssignmentChangeSerializer,
    DutyAssignmentGenerateSerializer,
    DutyAssignmentSerializer,
    DutyWithAssignmentsSerializer,
    StaffSerializer,
)
from .services.assignments import ManageAssignments
from .services.planner import Planner

logger = logging.getLogger(__name__)


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignments = ManageAssignments()

    def get_queryset(self) -> QuerySet:
        qs = self.assignments.get_all_staff()
        return qs


class DaysOffViewSet(viewsets.ModelViewSet):
    serializer_class = DaysOffSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignments = ManageAssignments()

    def get_queryset(self) -> QuerySet:
        query_params = self.request.query_params
        query_serializer = DatesQuerySerializer(data=query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data["start_date"] or None
        end_date = query_serializer.validated_data["end_date"] or None
        qs = self.assignments.get_days_off(start_date, end_date)
        return qs


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = DutyAssignmentSerializer

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.assignments = ManageAssignments()

    def get_queryset(self) -> QuerySet:
        qs = self.assignments.get_all_duty_assignments()
        return qs

    @action(detail=False, methods=["get"])
    def list_assignments(self, request) -> Response:
        query_serializer = DatesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data["start_date"]
        end_date = query_serializer.validated_data["end_date"]

        duties = self.assignments.get_duties_by_date(start_date, end_date)
        serializer = DutyWithAssignmentsSerializer(duties, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def generate(self, request) -> Response:
        parameters_serializer = DutyAssignmentGenerateSerializer(data=request.data)
        parameters_serializer.is_valid(raise_exception=True)

        people_per_day = parameters_serializer.validated_data["people_per_day"]
        serialized_dates = parameters_serializer.validated_data["dates"]

        dates = self.assignments.create_duty_days(serialized_dates)
        start_date, end_date = self.assignments.get_date_range(dates)
        plan = Planner(start_date, end_date, people_per_day)

        try:
            with transaction.atomic():
                errors = plan.create_plan()
                plan.set_minimum_priority()
                duties = self.assignments.get_duties_by_date(start_date, end_date)
                serializer = DutyWithAssignmentsSerializer(duties, many=True)
                data = {"errors": errors, "data": serializer.data}
                return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                data={"error": "Не удалось сгенерировать расписание: " + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=False, methods=["post"])
    def assign(self, request):
        duty_assignment_serializer = DutyAssignmentChangeSerializer(data=request.data)
        duty_assignment_serializer.is_valid(raise_exception=True)

        query_serializer = DatesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        prev_user = duty_assignment_serializer.validated_data["user_id_prev"]
        new_user = duty_assignment_serializer.validated_data["user_id_new"]
        date = duty_assignment_serializer.validated_data["date"]
        start_date = query_serializer.validated_data["start_date"]
        end_date = query_serializer.validated_data["end_date"]

        try:
            with transaction.atomic():
                logger.info("make assignment")
                if prev_user and new_user:
                    self.assignments.update_assignment(
                        duty_date=date, prev_user_id=prev_user, new_user_id=new_user
                    )
                elif prev_user is None and new_user:
                    self.assignments.create_assignment(duty_date=date, user_id=new_user)
                elif prev_user and new_user is None:
                    self.assignments.delete_assignment(
                        duty_date=date, user_id=prev_user
                    )
                logger.info("получаем duty")
                duties = self.assignments.get_duties_by_date(start_date, end_date)
                serializer = DutyWithAssignmentsSerializer(duties, many=True)
                return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Не удалось переназначить: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
