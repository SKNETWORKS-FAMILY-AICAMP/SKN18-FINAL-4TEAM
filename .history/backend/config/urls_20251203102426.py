from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
<<<<<<< HEAD
    path("api/stt/", include("stt.urls")),
=======
    path("mediapipe/", include("anti_cheat.urls")),
>>>>>>> cd7d63074ca89914ae1dbe3bff73314c77846e6b
]
