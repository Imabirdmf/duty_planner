from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import action
from .services.planner import create_plan


from .models import DaysOff, Duty, DutyAssignment, Staff
from .serializers import (
    CalendarMonthQuerySerializer,
    CalendarResponseSerializer,
    DaysOffSerializer,
    DutyAssignmentSerializer,
    # DutySerializer,
    StaffSerializer,
)

from .services.duty_calendar import save_duty_days, get_duty_days


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

    @action(detail=False, methods=['post'])
    def generate(self, request):
        parameters = request.data
        parameters_serializer = DutyAssignmentSerializer(parameters)
        parameters_serializer.is_valid()
        people_per_day = parameters_serializer.validated_data('people_per_day')
        message, errors = create_plan(people_per_day)

        return Response

    @action(detail=True, methods=['post'])
    def assignment(self, request):
        pass



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
        payload_serializer.is_valid()
        request_days_serialized = payload_serializer.validated_data["dates"]
        dates = save_duty_days(month_start, request_days_serialized)

        data = {"month": month_start, "dates": [duty.date for duty in dates]}
        response_serializer = CalendarResponseSerializer(data)

        return Response(response_serializer.data, status=status.HTTP_200_OK)
