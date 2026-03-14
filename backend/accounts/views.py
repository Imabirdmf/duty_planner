import logging

from django.conf import settings
from django.shortcuts import redirect
from invitations.utils import get_invitation_model
from rest_framework_simplejwt.tokens import RefreshToken

Invitation = get_invitation_model()

logger = logging.getLogger(__name__)


def accept_invitation(request, token):
    try:
        invitation = Invitation.objects.get(key=token)
        if invitation.accepted:
            return redirect(f"{settings.FRONTEND_URL}/invite-invalid")
        request.session["invitation_token"] = token
        return redirect("/accounts/google/login/")
    except Invitation.DoesNotExist:
        return redirect(f"{settings.FRONTEND_URL}/invite-invalid")


# def auth_complete(request):
#     user = request.user
#     if not user.is_authenticated:
#         return redirect(f"{settings.FRONTEND_URL}/login")
#     refresh = RefreshToken.for_user(user)
#     access_token = str(refresh.access_token)
#     refresh_token = str(refresh)
#     return redirect(
#         f"{settings.FRONTEND_URL}/auth/callback?access={access_token}&refresh={refresh_token}"
#     )
def auth_complete(request):
    print(
        f"=== auth_complete called, user: {request.user}, authenticated: {request.user.is_authenticated}"
    )
    user = request.user
    if not user.is_authenticated:
        logger.info("=== NOT AUTHENTICATED, redirecting to login")
        return redirect(f"{settings.FRONTEND_URL}/login")
    refresh = RefreshToken.for_user(user)
    access_token = str(refresh.access_token)
    refresh_token = str(refresh)
    url = f"{settings.FRONTEND_URL}/auth/callback?access={access_token}&refresh={refresh_token}"
    print(f"=== redirecting to: {url}")
    return redirect(url)
