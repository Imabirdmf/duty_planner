import os
import dj_database_url
from .base import *  # noqa: F403

DEBUG = False


ALLOWED_HOSTS = [
    "dutyplannerfrontend-production.up.railway.app",
    "dutyplannerbackend-production.up.railway.app",
    "dutyplannerfrontend.railway.internal",
    "dutyplannerbackend.railway.internal",
    "dutyplannerfrontend-staging.up.railway.app",
    "dutyplannerbackend-staging.up.railway.app"
]