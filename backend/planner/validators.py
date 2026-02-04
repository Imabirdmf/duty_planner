from rest_framework import serializers
from django.core import validators
from django.utils import timezone

def validate_date_not_past(value):
    if value < timezone.localdate():
        raise serializers.ValidationError(
            "Нельзя добавить дату из прошлого"
        )
    return value