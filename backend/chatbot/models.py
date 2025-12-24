from django.db import models
from api.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, db_column="user_id")
    role = models.CharField(max_length=100, null=True, blank=True)
    target_company = models.CharField(max_length=255, null=True, blank=True)
    weekly_hours = models.PositiveSmallIntegerField(null=True, blank=True)
    skill_level = models.CharField(max_length=50, null=True, blank=True)
    preferred_langs = models.JSONField(null=True, blank=True)  # list of strings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_profile"


class UserWeeklyPlan(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    week_id = models.CharField(max_length=50)
    goals = models.JSONField(null=True, blank=True)
    routines = models.JSONField(null=True, blank=True)
    focus_areas = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)  # active/done 등
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_weekly_plan"
        constraints = [
            models.UniqueConstraint(fields=["user", "week_id"], name="uq_user_week")
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_weekly_plan_status"),
        ]


class UserResearchBrief(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    brief_id = models.CharField(max_length=100)
    topic = models.CharField(max_length=255, null=True, blank=True)
    summary = models.TextField(null=True, blank=True)
    actions = models.JSONField(null=True, blank=True)
    sources = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_research_briefs"
        constraints = [
            models.UniqueConstraint(fields=["user", "brief_id"], name="uq_user_brief")
        ]
        indexes = [
            models.Index(fields=["user", "topic"], name="idx_research_briefs_topic"),
        ]


class UserNextAction(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    action_id = models.CharField(max_length=100)
    title = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    due = models.DateTimeField(null=True, blank=True)
    priority = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)  # todo/doing/done
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "user_next_actions"
        constraints = [
            models.UniqueConstraint(fields=["user", "action_id"], name="uq_user_action")
        ]
        indexes = [
            models.Index(fields=["user", "status"], name="idx_next_actions_status"),
        ]


class UserOutcomeLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    outcome_id = models.CharField(max_length=100)
    kind = models.CharField(max_length=50, null=True, blank=True)  # PR/blog/ct 등
    summary = models.TextField(null=True, blank=True)
    link = models.TextField(null=True, blank=True)
    score = models.JSONField(null=True, blank=True)  # 점수/오답 패턴/시간 등
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_outcome_logs"
        constraints = [
            models.UniqueConstraint(fields=["user", "outcome_id"], name="uq_user_outcome")
        ]
        indexes = [
            models.Index(fields=["user", "kind"], name="idx_outcome_logs_kind"),
        ]


class UserCoachingLog(models.Model):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    coaching_id = models.CharField(max_length=100)
    artifact_id = models.CharField(max_length=100, null=True, blank=True)
    findings = models.JSONField(null=True, blank=True)
    recommendations = models.JSONField(null=True, blank=True)
    rubric_scores = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "user_coaching_logs"
        constraints = [
            models.UniqueConstraint(fields=["user", "coaching_id"], name="uq_user_coaching")
        ]


class MemoriesTraits(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, db_column="user_id")
    strengths = models.JSONField(null=True, blank=True)
    weaknesses = models.JSONField(null=True, blank=True)
    patterns = models.JSONField(null=True, blank=True)
    confidence = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memories_traits"


class MemoriesPreferences(models.Model):
    user = models.OneToOneField(User, primary_key=True, on_delete=models.CASCADE, db_column="user_id")
    tone_pref = models.CharField(max_length=50, null=True, blank=True)
    detail_level = models.CharField(max_length=50, null=True, blank=True)
    feedback_style = models.CharField(max_length=50, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "memories_preferences"
