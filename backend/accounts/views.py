# Create your views here.
import os

from accounts.models import Invitation, User
from accounts.serializers import EmailRegisterSerializer
from dj_rest_auth.jwt_auth import set_jwt_cookies
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken


class CreateInvitationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        invitation = Invitation.objects.create(created_by=request.user)
        tkn = invitation.token
        return Response(
            {"url": f'{os.environ.get("FRONTEND_URL")}/register?token={tkn}'},
            status=status.HTTP_201_CREATED,
        )


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serialized_data = EmailRegisterSerializer(data=request.data)
        serialized_data.is_valid(raise_exception=True)
        if User.objects.filter(email=serialized_data.validated_data["email"]).exists():
            return Response(
                {"email": ["A user with this email already exists."]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = User.objects.create_user(
            email=serialized_data.validated_data["email"],
            password=serialized_data.validated_data["password1"],
        )
        refresh = RefreshToken.for_user(user)
        access = refresh.access_token

        response = Response({"user": {"email": user.email}}, status=201)
        set_jwt_cookies(response, access_token=access, refresh_token=refresh)
        return response
