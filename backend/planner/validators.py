from django.utils import timezone
from rest_framework import serializers


def validate_date_not_past(value):
    if value < timezone.localdate():
        raise serializers.ValidationError("Нельзя добавить дату из прошлого")
    return value
