from .base import *  # noqa: F403

DEBUG = False
ALLOWED_HOSTS = ["*"]


REST_AUTH = {
    "REGISTER_SERIALIZER": "accounts.serializers.EmailRegisterSerializer",
    "USE_JWT": True,
    "JWT_AUTH_COOKIE": "auth-token",  # имя куки для access токена
    "JWT_AUTH_REFRESH_COOKIE": "refresh-token",  # имя куки для refresh токена
    "JWT_AUTH_HTTPONLY": True,  # HttpOnly — JS не видит куки
    "JWT_AUTH_SAMESITE": "Lax",  # защита от CSRF
    "JWT_AUTH_SECURE": True,
    "TOKEN_MODEL": None,
}
