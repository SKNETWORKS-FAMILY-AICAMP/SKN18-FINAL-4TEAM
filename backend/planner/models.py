from django.db import models
from api.models import User

class StudyPlan(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id", to_field="user_id")
    topic = models.CharField(max_length=200)
    duration = models.IntegerField(default=7)
    created_at = models.DateTimeField(auto_now_add=True)

class DailyTask(models.Model):
    plan = models.ForeignKey(StudyPlan, related_name='tasks', on_delete=models.CASCADE)
    day = models.IntegerField()
    topic = models.CharField(max_length=255)
    video_title = models.CharField(max_length=255, null=True, blank=True)
    video_url = models.URLField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
