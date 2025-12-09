from django.urls import path
from .views import run_stt, transcribe_only

urlpatterns = [
    path("run/", run_stt, name="run_stt"),
    path("transcribe/", transcribe_only, name="stt_transcribe"),
]
