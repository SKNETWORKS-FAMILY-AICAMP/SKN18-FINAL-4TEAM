from django.urls import path

from .views import health, roadmap

urlpatterns = [
    path("health/", health, name="health"),
    path("roadmap/", roadmap, name="roadmap"),
]
