from django.urls import path
from .views import EmailSendView, EmailVerifyView, GoogleAuthView, SignupView, health, roadmap

from .views import (
    EmailSendView,
    EmailVerifyView,
    FindIdView,
    FindPasswordView,
    GoogleAuthView,
    LiveCodingSessionView,
    LoginView,
    RandomCodingProblemView,
    SignupView,
    UserIdCheckView,
    health,
    roadmap,
)
urlpatterns = [
    path("health/", health, name="health"),
    path("roadmap/", roadmap, name="roadmap"),
    path("coding-test/session/", LiveCodingSessionView.as_view(), name="coding-session"),
    path("auth/signup/", SignupView.as_view(), name="signup"),
    path("auth/user-id/check/", UserIdCheckView.as_view(), name="user-id-check"),
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/find-id/", FindIdView.as_view(), name="find-id"),
    path("auth/find-password/", FindPasswordView.as_view(), name="find-password"),
    path("auth/email/send/", EmailSendView.as_view(), name="email-send"),
    path("auth/email/verify/", EmailVerifyView.as_view(), name="email-verify"),
    path("auth/google/", GoogleAuthView.as_view(), name="google-auth"),
    # 랜덤 문제 전용 엔드포인트 (세션 로직 호출하지 않음)
    path("coding-problems/random/", RandomCodingProblemView.as_view(), name="coding-problem-random"),
]
