from django.db import models
from api.models import User

try:
    from django.contrib.postgres.fields import ArrayField
except Exception:  # pragma: no cover - postgres extension 미사용 시
    ArrayField = None

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
    reflection_difficulty = models.PositiveSmallIntegerField(null=True, blank=True)
    lecture_note = models.CharField(blank=True, default="")


class RecommendedVideo(models.Model):
    """
    docker/init.sql 에 정의된 recommended_videos 테이블 매핑
    """
    id = models.AutoField(primary_key=True)
    code_lang = ArrayField(models.TextField(), null=True, blank=True) if ArrayField else models.JSONField(null=True, blank=True)
    video_url = models.URLField(max_length=200)
    summary = models.TextField()
    category = ArrayField(models.TextField(), default=list) if ArrayField else models.JSONField(default=list)
    domain = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "recommended_videos"
