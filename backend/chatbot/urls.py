from django.urls import path

from .views import CoachChatView

urlpatterns = [
    path("coach/", CoachChatView.as_view(), name="chatbot-coach"),
]
