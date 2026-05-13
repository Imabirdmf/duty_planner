from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["*"]


REST_AUTH = {
    **REST_AUTH,  # noqa: F405
    "JWT_AUTH_SECURE": True,
    "JWT_AUTH_SAMESITE": 'None'
}

SESSION_COOKIE_SAMESITE = 'None'
SESSION_COOKIE_SECURE = True

CORS_ALLOWED_ORIGINS = [
    "https://dutyplannerbackend-staging.up.railway.app",
    "https://dutyplannerfrontend-staging.up.railway.app",
    "https://dutyplannerfrontend-production.up.railway.app",
    "https://dutyplannerbackend-production.up.railway.app",
]

CSRF_TRUSTED_ORIGINS = [
    "https://dutyplannerbackend-production.up.railway.app",
    'https://dutyplannerfrontend-production.up.railway.app/',
    "https://dutyplannerbackend-staging.up.railway.app",
    'https://dutyplannerfrontend-staging.up.railway.app/'
]