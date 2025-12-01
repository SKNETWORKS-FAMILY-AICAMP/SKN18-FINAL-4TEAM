from django.urls import path

from .views import EmailSendView, EmailVerifyView, GoogleAuthView, SignupView, health, roadmap

urlpatterns = [
    path("health/", health, name="health"),
    path("roadmap/", roadmap, name="roadmap"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/email/send/", EmailSendView.as_view(), name="email-send"),
    path("auth/email/verify/", EmailVerifyView.as_view(), name="email-verify"),
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
]
