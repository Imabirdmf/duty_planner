import logging

from allauth.core.exceptions import SignupClosedException
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from invitations.utils import get_invitation_model

logger = logging.getLogger(__name__)
Invitation = get_invitation_model()


class InvitationSocialAccountAdapter(DefaultSocialAccountAdapter):
    def is_open_for_signup(self, request, sociallogin):
        if sociallogin.is_existing:
            return True

        invite_token = request.session.get("invitation_token")
        if not invite_token:
            raise SignupClosedException()
        try:
            invitation = Invitation.objects.get(key=invite_token)
            if invitation.accepted:
                raise SignupClosedException()
        except Invitation.DoesNotExist:
            raise SignupClosedException()
        return True

    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)
        invite_token = request.session.get("invitation_token")
        if invite_token:
            try:
                invitation = Invitation.objects.get(key=invite_token)
                invitation.accepted = True
                invitation.save()
                del request.session["invitation_token"]
            except Invitation.DoesNotExist:
                pass
        return user
