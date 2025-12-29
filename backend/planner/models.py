from django.db import models
from django.conf import settings

class StudyPlan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
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