import os

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class AccountsConfig(AppConfig):
    name = "accounts"

    def ready(self):
        front_url = os.environ.get("FRONTEND_URL")
        if not front_url:
            raise ImproperlyConfigured("Frontend application is improperly configured")
