from rest_framework import viewsets

from .models import Staff
from .serializers import StaffSerializer


# Create your views here.
class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
