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


class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer

    def get_queryset(self):
        from planner.services.repositories.staff_repository import StaffRepository

        staff_repo = StaffRepository()
        return staff_repo.get_all()


class DaysOffViewSet(viewsets.ModelViewSet):
    serializer_class = DaysOffSerializer

    def get_queryset(self):
        from planner.services.repositories.days_off_repository import DaysOffRepository

        daysoff_repo = DaysOffRepository()

        query_params = self.request.query_params
        start_date = query_params.get("start_date", None)
        end_date = query_params.get("end_date", None)
        if start_date and end_date:
            qs = daysoff_repo.get_list_of_days_off(start_date, end_date)
        else:
            qs = daysoff_repo.get_all()
        return qs


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    serializer_class = DutyAssignmentSerializer

    def get_queryset(self):
        from planner.services.repositories.duty_assignment_repository import (
            DutyAssignmentRepository,
        )

        duty_assignment_repo = DutyAssignmentRepository()
        return duty_assignment_repo.get_all()

    @action(detail=False, methods=["get"])
    def list_assignments(self, request):
        assignments = ManageAssignments()
        query_serializer = DatesQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)

        start_date = query_serializer.validated_data["start_date"]
        end_date = query_serializer.validated_data["end_date"]

        duties = assignments.get_duties(start_date, end_date)
        serializer = DutyWithAssignmentsSerializer(duties, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"])
    def generate(self, request):
        parameters_serializer = DutyAssignmentGenerateSerializer(data=request.data)
        parameters_serializer.is_valid(raise_exception=True)

        people_per_day = parameters_serializer.validated_data["people_per_day"]
        serialized_dates = parameters_serializer.validated_data["dates"]

        assignments = ManageAssignments()
        dates = assignments.create_duty_days(serialized_dates)
        start_date = dates[0]
        end_date = dates[-1]
        plan = Planner(start_date, end_date, people_per_day)

        try:
            errors = plan.create_plan()
            plan.set_minimum_priority()
            duties = assignments.get_duties(start_date, end_date)
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

        assignments = ManageAssignments()
        try:
            print("make assignment")
            assignments.make_assignment(
                prev_user=prev_user, new_user=new_user, duty_date=date
            )
            print("получаем duty")
            duties = assignments.get_duties(start_date, end_date)
            serializer = DutyWithAssignmentsSerializer(duties, many=True)
            return Response({"data": serializer.data}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": f"Не удалось переназначить: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
