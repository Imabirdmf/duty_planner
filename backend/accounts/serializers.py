from accounts.models import Invitation
from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
class EmailRegisterSerializer(RegisterSerializer):
    username = None
    token = serializers.UUIDField(required=True)

    def get_cleaned_data(self):
        return {
            "email": self.validated_data.get("email", ""),
            "password1": self.validated_data.get("password1", ""),
        }

    def validate(self, data):
        tkn = data.get("token")
        try:
            invitation = Invitation.objects.get(token=tkn)
            if not invitation.is_valid():
                raise ValidationError("Invitation has expired")
        except Invitation.DoesNotExist:
            raise ValidationError("Invalid invitation token")
        return data
