from django.urls import path
from .views import EmailSendView, EmailVerifyView, GoogleAuthView, SignupView, health, roadmap
from .views import (
    EmailSendView,
    EmailVerifyView,
    FindIdView,
    FindPasswordView,
    GoogleAuthView,
    LoginView,
    SignupView,
    UserIdCheckView,
    health,
    roadmap,
)

urlpatterns = [
    path("health/", health, name="health"),
    path("roadmap/", roadmap, name="roadmap"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/user-id/check/", UserIdCheckView.as_view(), name="user-id-check"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/find-id/", FindIdView.as_view(), name="find-id"),
    path("auth/find-password/", FindPasswordView.as_view(), name="find-password"),
    path("auth/email/send/", EmailSendView.as_view(), name="email-send"),
    path("auth/email/verify/", EmailVerifyView.as_view(), name="email-verify"),
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
]