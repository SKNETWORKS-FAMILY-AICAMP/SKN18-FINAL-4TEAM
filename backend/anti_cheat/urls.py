from django.urls import path

from .views import CheatAnalysisView, FacePresenceView

urlpatterns = [
    path("analyze/", CheatAnalysisView.as_view(), name="mediapipe-analyze"),
    path("presence/", FacePresenceView.as_view(), name="mediapipe-presence"),
]
