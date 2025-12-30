from django.urls import path
from .views import GeneratePlanView, LatestStudyPlanView, StudyTaskCompletionView, StudyTaskReflectionView

urlpatterns = [
    path("generate-plan/", GeneratePlanView.as_view(), name="generate-plan"),
    path("plans/latest/", LatestStudyPlanView.as_view(), name="studyplan-latest"),
    path("tasks/complete/", StudyTaskCompletionView.as_view(), name="studyplan-task-complete"),
    path("tasks/reflection/", StudyTaskReflectionView.as_view(), name="studyplan-task-reflection"),
]
