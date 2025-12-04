from django.urls import path

from .views import (
    EmailSendView,
    EmailVerifyView,
    CodingProblemSessionInitView,
    FindIdView,
    FindPasswordView,
    GoogleAuthView,
    LoginView,
    RandomCodingProblemView,
    SignupView,
    UserIdCheckView,
    WarmupLanggraphView,
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
    path("coding-problems/random/", RandomCodingProblemView.as_view(), name="coding-problem-random"),
    path(
        "coding-problems/random/session/",
        CodingProblemSessionInitView.as_view(),
        name="coding-problem-random-session",
    ),
    path("warmup/langgraph/", WarmupLanggraphView.as_view(), name="warmup-langgraph"),
]
