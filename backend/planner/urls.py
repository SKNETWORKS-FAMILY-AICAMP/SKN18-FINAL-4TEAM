from django.urls import path
from .views import GeneratePlanView, LatestStudyPlanView, StudyTaskReflectionView

urlpatterns = [
    path("generate-plan/", GeneratePlanView.as_view(), name="generate-plan"),
    path("plans/latest/", LatestStudyPlanView.as_view(), name="studyplan-latest"),
    path("tasks/reflection/", StudyTaskReflectionView.as_view(), name="studyplan-task-reflection"),
]
