from django.db import transaction
from django.shortcuts import get_list_or_404
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import DaysOff, DutyAssignment, Staff
from .serializers import (
    DaysOffSerializer,
    DutyAssignmentChangeSerializer,
    DutyAssignmentGenerateSerializer,
    DatesQuerySerializer,
    DutyAssignmentSerializer,
    DutyWithAssignmentsSerializer,
    StaffSerializer,
)
from .services.assignments import get_assignments, make_assignment
from .services.duty_calendar import save_duty_days
from .services.planner import create_plan, set_minimum_priority


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class DaysOffViewSet(viewsets.ModelViewSet):
    queryset = DaysOff.objects.all()
    serializer_class = DaysOffSerializer

    def get_queryset(self):
        query_params = self.request.query_params
        start_date = query_params.get('start_date', None)
        end_date = query_params.get('end_date', None)
        if start_date and end_date:
            qs = get_list_or_404(DaysOff, date__gte=start_date, date__lte=end_date)
        else:
            qs = DaysOff.objects.all()
        return qs


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DutyAssignment.objects.all()
    serializer_class = DutyAssignmentSerializer

    @action(detail=False, methods=["get"])
    def list_assignments(self, request):
        query_serializer = DatesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data["start_date"]
        end_date = query_serializer.validated_data["end_date"]

        duties = get_assignments(start_date, end_date)
        serializer = DutyWithAssignmentsSerializer(duties, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        parameters_serializer = DutyAssignmentGenerateSerializer(data=request.data)
        parameters_serializer.is_valid(raise_exception=True)

        people_per_day = parameters_serializer.validated_data["people_per_day"]
        serialized_dates = parameters_serializer.validated_data["dates"]

        with transaction.atomic():
            dates = save_duty_days(serialized_dates)
            start_day = dates[0].date
            end_day = dates.last().date

            try:
                errors = create_plan(start_day, end_day, people_per_day)
                set_minimum_priority()
                duties = get_assignments(start_day, end_day)
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
            print("Меняю назначение")
            make_assignment(prev_user=prev_user, new_user=new_user, duty_date=date)
            print("Получаю назначения")
            duties = get_assignments(start_date, end_date)
            serializer = DutyWithAssignmentsSerializer(duties, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Не удалось переназначить: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

