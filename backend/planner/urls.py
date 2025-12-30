from django.urls import path
from .views import GeneratePlanView, LatestStudyPlanView, StudyTaskCompletionView

urlpatterns = [
    path("generate-plan/", GeneratePlanView.as_view(), name="generate-plan"),
    path("plans/latest/", LatestStudyPlanView.as_view(), name="studyplan-latest"),
    path("tasks/complete/", StudyTaskCompletionView.as_view(), name="studyplan-task-complete"),
]
