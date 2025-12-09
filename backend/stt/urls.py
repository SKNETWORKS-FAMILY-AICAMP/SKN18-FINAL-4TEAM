from django.urls import path
from .views import transcribe_only

urlpatterns = [
    path("transcribe/", transcribe_only, name="stt_transcribe"),
]
