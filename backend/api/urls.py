from django.urls import path

from .views import (
    EmailSendView,
    EmailVerifyView,
    FindIdView,
    FindPasswordView,
    GoogleAuthView,
    LoginView,
    LogoutView,
    LiveCodingActiveSessionView,
    LiveCodingEndSessionView,
    LiveCodingCodeSnapshotView,
    LiveCodingSessionView,
    LiveCodingStartView,
    SignupView,
    UserIdCheckView,
    UserMeView,
    ProfileView,
    health,
    roadmap,
)

from .chap1_views import (
    CodingProblemTextInitView,
    LiveCodingPreloadView,
    InterviewIntroEventView,
    WarmupLanggraphView,
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
    path("auth/me/", UserMeView.as_view(), name="me"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    
    # langgraph에서 사용
    path("warmup/langgraph/", WarmupLanggraphView.as_view(), name="warmup-langgraph"),
    path("livecoding/preload/", LiveCodingPreloadView.as_view(), name="livecoding-preload"),
    path("coding-problems/session/init/",CodingProblemTextInitView.as_view(),name="coding-problem-session-init-text",),
    path("livecoding/start/", LiveCodingStartView.as_view(), name="livecoding-start"),
    path("interview/event/",InterviewIntroEventView.as_view(),name="interview-event",),
    
    # livecoding 관련 
    path("livecoding/session/", LiveCodingSessionView.as_view(), name="livecoding-session"),
    path("livecoding/session/active/", LiveCodingActiveSessionView.as_view(), name="livecoding-session-active"),
    path("livecoding/session/end/", LiveCodingEndSessionView.as_view(), name="livecoding-session-end"),
    path( "livecoding/session/code/", LiveCodingCodeSnapshotView.as_view(),name="livecoding-session-code",),
    
    # profile
    path("user/profile/", ProfileView.as_view(), name="profile"),
]
