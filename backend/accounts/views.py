# Create your views here.
import base64
import hashlib
import os
import secrets

from accounts.models import Invitation, User
from accounts.serializers import EmailRegisterSerializer
from dj_rest_auth.jwt_auth import set_jwt_cookies
from django.http import HttpResponse
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from google_auth_oauthlib.flow import Flow
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

GOOGLE_REDIRECT_URI = os.environ.get(
    "GOOGLE_REDIRECT_URI"
)

GOOGLE_CLIENT_CONFIG = {
    "web": {
        "client_id": os.environ.get("GOOGLE_CLIENT_ID"),
        "client_secret": os.environ.get("GOOGLE_CLIENT_SECRET"),
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
    }
}

GOOGLE_SCOPES = [
    "openid",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]


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


class GoogleLoginView(APIView):
    def post(self, request):
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        code_verifier = secrets.token_urlsafe(64)
        code_challenge = (
            base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode()).digest())
            .rstrip(b"=")
            .decode()
        )

        request.session["google_code_verifier"] = code_verifier

        auth_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            code_challenge=code_challenge,
            code_challenge_method="S256",
        )

        request.session["google_oauth_state"] = state
        return Response({"url": auth_url})


class GoogleCallbackView(APIView):
    def get(self, request):
        state = request.query_params.get("state")
        code = request.query_params.get("code")
        if state != request.session.get("google_oauth_state"):
            return Response({"error": "Invalid state"}, status=400)
        flow = Flow.from_client_config(
            GOOGLE_CLIENT_CONFIG,
            scopes=GOOGLE_SCOPES,
            redirect_uri=GOOGLE_REDIRECT_URI,
        )
        code_verifier = request.session.get("google_code_verifier")
        try:
            flow.fetch_token(code=code, code_verifier=code_verifier)
        except Exception:
            return Response({"error": "Failed to exchange code for token"}, status=400)

        try:
            id_info = id_token.verify_oauth2_token(
                flow.credentials.id_token,
                google_requests.Request(),
                os.environ.get("GOOGLE_CLIENT_ID"),
            )
        except Exception:
            return Response({"error": "Failed to verify Google token"}, status=400)

        email = id_info.get("email")
        if not email:
            return Response({"error": "No email provided by Google"}, status=400)

        allowed_domain = os.environ.get("GOOGLE_ALLOWED_DOMAIN")
        email_domain = email.lower().split("@")[-1]
        if allowed_domain and email_domain != allowed_domain.lower():
            frontend_url = os.environ.get("FRONTEND_URL", "*")
            response = HttpResponse(
                f"""
                <html><body><script>
                    window.opener.postMessage('google-auth-error:domain-not-allowed', '{frontend_url}');
                    window.close();
                </script></body></html>
            """,
                content_type="text/html",
            )
            response["Cross-Origin-Opener-Policy"] = "unsafe-none"
            return response

        user, created = User.objects.get_or_create(email=email)
        if created:
            user.set_unusable_password()  # Google пользователь, пароль не нужен
            user.save()

        refresh = RefreshToken.for_user(user)
        access = refresh.access_token
        frontend_url = os.environ.get("FRONTEND_URL", "*")
        response = HttpResponse(
            f"""
            <html><body><script>
                window.opener.postMessage('google-auth-success', '{frontend_url}');
                window.close();
            </script></body></html>
        """,
            content_type="text/html",
        )

        response["Cross-Origin-Opener-Policy"] = "unsafe-none"
        set_jwt_cookies(response, access_token=access, refresh_token=refresh)

        return response
