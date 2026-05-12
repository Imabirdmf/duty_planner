import os

from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class CommonAppConfig(AppConfig):
    name = "common_app"

    def ready(self):

        for x in (
            "JIRA_BASE_URL",
            "JIRA_API_TOKEN",
            "JIRA_PROJECT_KEY",
            "JIRA_EMAIL",
            "JIRA_PARENT_ISSUE_KEY",
        ):
            if not os.environ.get(x):
                raise ImproperlyConfigured(f"{x} is improperly configured")
