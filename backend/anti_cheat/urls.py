from django.urls import path

from .views import CheatAnalysisView

urlpatterns = [
    path("analyze/", CheatAnalysisView.as_view(), name="mediapipe-analyze"),
]

