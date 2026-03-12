from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers


class EmailRegisterSerializer(RegisterSerializer):
    username = None

    def get_cleaned_data(self):
        return {
            'email': self.validated_data.get('email', ''),
            'password1': self.validated_data.get('password1', ''),
        }