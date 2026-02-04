from rest_framework import viewsets
from rest_framework.validators import UniqueTogetherValidator

from .models import Staff, DaysOff
from .serializers import StaffSerializer, DaysOffSerializer


class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer

class DaysOffViewSet(viewsets.ModelViewSet):
    queryset = DaysOff.objects.all()
    serializer_class = DaysOffSerializer

