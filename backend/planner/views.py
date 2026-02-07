from rest_framework import status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import DaysOff, Duty, DutyAssignment, Staff
from .serializers import (
    CalendarMonthQuerySerializer,
    CalendarResponseSerializer,
    DaysOffSerializer,
    DutyAssignmentSerializer,
    DutySerializer,
    StaffSerializer,
)
from .services import calendar


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer


class DaysOffViewSet(viewsets.ModelViewSet):
    queryset = DaysOff.objects.all()
    serializer_class = DaysOffSerializer


class DutyViewSet(viewsets.ModelViewSet):
    queryset = Duty.objects.all()
    serializer_class = DutySerializer


class DutyAssignmentViewSet(viewsets.ModelViewSet):
    queryset = DutyAssignment.objects.all()
    serializer_class = DutyAssignmentSerializer


class CalendarView(APIView):

    def get(self, request):
        serializer = CalendarMonthQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        month_start = serializer.validated_data["month"]

        duty_dates = calendar.get_duty_days(month_start)
        dates = [d.date for d in duty_dates]
        data = {
            "month": month_start,
            "dates": dates}

        response_serializer = CalendarResponseSerializer(data)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
