from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/stt/", include("stt.urls")),
    path("mediapipe/", include("anti_cheat.urls")),
    path("api/", include("api.urls")),
]
