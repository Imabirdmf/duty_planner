from rest_framework import viewsets

from .models import DaysOff, Duty, DutyAssignment, Staff
from .serializers import (
    DaysOffSerializer,
    DutyAssignmentSerializer,
    DutySerializer,
    StaffSerializer,
)


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
