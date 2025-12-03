from django.urls import path
from .views import run_stt

urlpatterns = [
    path("run/", run_stt, name="run_stt"),
]