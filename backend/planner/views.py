from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DaysOff, DutyAssignment, Staff
from .serializers import (
    CalendarMonthQuerySerializer,
    CalendarResponseSerializer,
    DaysOffSerializer,
    DutyAssignmentChangeSerializer,
    DutyAssignmentSerializer,
    # DutySerializer,
    StaffSerializer,
)
from .services.assignments import make_assignment
from .services.duty_calendar import get_duty_days, save_duty_days
from .services.planner import create_plan


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class DaysOffViewSet(viewsets.ModelViewSet):
    queryset = DaysOff.objects.all()
    serializer_class = DaysOffSerializer


# class DutyViewSet(viewsets.ModelViewSet):
#     queryset = Duty.objects.all()
#     serializer_class = DutySerializer


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DutyAssignment.objects.all()
    serializer_class = DutyAssignmentSerializer

    @action(detail=False, methods=["post"])
    def generate(self, request):
        parameters_serializer = DutyAssignmentSerializer(request.data)
        parameters_serializer.is_valid(raise_exception=True)
        people_per_day = parameters_serializer.validated_data["people_per_day"]
        message, errors = create_plan(people_per_day)
        data = {"message": message, "errors": errors}

        return Response(data)

    @action(detail=False, methods=["post"])
    def assign(self, request):
        duty_assignment = DutyAssignmentChangeSerializer(request.data)
        duty_assignment.is_valid(raise_exception=True)
        prev_user = duty_assignment.validated_data["prev_user"]
        new_user = duty_assignment.validated_data["new_user"]
        date = duty_assignment.validated_data["date"]
        try:
            make_assignment(prev_user=prev_user, new_user=new_user, duty_date=date)
        except Exception as e:
            return Response(
                {"error": "Не удалось переназначить: " + str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"status": "updated"}, status=status.HTTP_200_OK)


class CalendarView(APIView):

    def get(self, request):
        serializer = CalendarMonthQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        month_start = serializer.validated_data["month"]

        duty_dates = get_duty_days(month_start)
        dates = [d.date for d in duty_dates]
        data = {"month": month_start, "dates": dates}

        response_serializer = CalendarResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        serializer = CalendarMonthQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        month_start = serializer.validated_data["month"]

        request_days = request.data
        payload_serializer = CalendarResponseSerializer(data=request_days)
        payload_serializer.is_valid(raise_exception=True)
        request_days_serialized = payload_serializer.validated_data["dates"]
        dates = save_duty_days(month_start, request_days_serialized)

        data = {"month": month_start, "dates": [duty.date for duty in dates]}
        response_serializer = CalendarResponseSerializer(data)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
