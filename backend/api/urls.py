from django.urls import path
from .views import health, roadmap, start_livecoding

urlpatterns = [
    path("health/", health, name="health"),
    path("roadmap/", roadmap, name="roadmap"),
    path("livecoding/start/", start_livecoding, name="livecoding-start"),
]
