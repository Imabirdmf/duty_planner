import os

import dj_database_url

from .base import *  # noqa: F403

DEBUG = False
DATABASES = {"default": dj_database_url.config(default=os.environ.get("DATABASE_URL"))}
ALLOWED_HOSTS = [
    "dutyplannerfrontend-staging.up.railway.app",
    "https://dutyplannerfrontend-production.up.railway.app/",
]
