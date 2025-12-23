from django.db import models


class User(models.Model):
  user_id = models.CharField(primary_key=True, max_length=50, db_column="user_id")
  email = models.EmailField(unique=True)
  name = models.CharField(max_length=50)
  phone_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
  password_hash = models.CharField(max_length=255, null=True, blank=True)
  birthdate = models.DateField(null=True, blank=True)
  created_at = models.DateTimeField(null=True, blank=True)
  updated_at = models.DateTimeField(null=True, blank=True)

  @property
  def is_authenticated(self) -> bool:
    return True

  class Meta:
    managed = False
    db_table = "users"


class AuthIdentity(models.Model):
  id = models.AutoField(primary_key=True)
  user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
  provider = models.CharField(max_length=20)
  provider_user_id = models.CharField(max_length=255)
  refresh_token = models.TextField(null=True, blank=True)
  token_expires_at = models.DateTimeField(null=True, blank=True)
  scope = models.TextField(null=True, blank=True)
  created_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = False
    db_table = "auth_identities"
    unique_together = (("provider", "provider_user_id"), ("user", "provider"))
    indexes = [
      models.Index(fields=["provider", "provider_user_id"], name="auth_id_provider_user_idx"),
    ]


class EmailVerification(models.Model):
  id = models.AutoField(primary_key=True)
  email = models.EmailField(unique=True)
  code = models.CharField(max_length=16)
  expires_at = models.DateTimeField(null=True, blank=True)
  verified_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    db_table = "email_verifications"


class CodingProblem(models.Model):
  problem_id = models.IntegerField(primary_key=True)
  problem = models.TextField()
  difficulty = models.CharField(max_length=50)
  category = models.CharField(max_length=100)

  class Meta:
    managed = False
    db_table = "coding_problem"


class CodingProblemLanguage(models.Model):
  id = models.IntegerField(primary_key=True)
  problem = models.ForeignKey(
      CodingProblem,
      on_delete=models.CASCADE,
      db_column="problem_id",
      related_name="languages",
  )
  function_name = models.CharField(max_length=255)
  starter_code = models.TextField()
  language = models.CharField(max_length=50)

  class Meta:
    managed = False
    db_table = "coding_problem_language"


class TestCase(models.Model):
  id = models.IntegerField(primary_key=True)
  problem = models.ForeignKey(
      CodingProblem,
      on_delete=models.CASCADE,
      db_column="problem_id",
      related_name="test_cases",
  )
  input_data = models.TextField(db_column="input")
  output_data = models.TextField(db_column="output")

  class Meta:
    managed = False
    db_table = "test_case"

class LivecodingReport(models.Model):
    id = models.AutoField(primary_key=True)
    session_id = models.CharField(max_length=100, unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, db_column="user_id")
    report_md = models.TextField()
    final_score = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    final_grade = models.CharField(max_length=8, null=True, blank=True)
    final_flags = models.JSONField(default=list)
    graph_output = models.JSONField(default=dict)
    problem_eval_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    problem_eval_feedback = models.TextField(null=True, blank=True)
    code_collab_score = models.DecimalField(max_digits=6, decimal_places=4, null=True, blank=True)
    code_collab_feedback = models.TextField(null=True, blank=True)
    problem_evidence = models.JSONField(null=True, blank=True)
    code_collab_evidence = models.JSONField(null=True, blank=True)
    step = models.CharField(max_length=20, null=True, blank=True)
    status = models.CharField(max_length=20, null=True, blank=True)
    error = models.TextField(null=True, blank=True)
    pdf_path = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "livecoding_reports"
        indexes = [models.Index(fields=["user", "session_id"], name="idx_lc_report_user_sess")]
