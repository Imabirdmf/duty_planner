"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from accounts.views import (
    CreateInvitationView,
    GoogleCallbackView,
    GoogleLoginView,
    RegisterView,
)
from django.contrib import admin
from django.urls import include, path
from planner.views import (
    DaysOffViewSet,
    DutyAssignmentViewSet,
    StaffViewSet,
)
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register("users", StaffViewSet, basename="users")
router.register("days-off", DaysOffViewSet, basename="days-off")
router.register("duties", DutyAssignmentViewSet, basename="duty-assignments")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(router.urls)),
    path("api/auth/", include("dj_rest_auth.urls")),
    path("api/auth/registration/", RegisterView.as_view()),
    path("api/auth/invite/", CreateInvitationView.as_view()),
    path("api/auth/google/", GoogleLoginView.as_view()),
    path("api/auth/google/callback/", GoogleCallbackView.as_view()),
]
