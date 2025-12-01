from django.db import models


class User(models.Model):
  user_id = models.AutoField(primary_key=True)
  email = models.EmailField(unique=True)
  name = models.CharField(max_length=50)
  phone_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
  password_hash = models.CharField(max_length=255, null=True, blank=True)
  birthdate = models.DateField(null=True, blank=True)
  created_at = models.DateTimeField(null=True, blank=True)
  updated_at = models.DateTimeField(null=True, blank=True)

  class Meta:
    managed = False  # 테이블은 init.sql에서 생성됨
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
    managed = False  # 테이블은 init.sql에서 생성됨
    db_table = "auth_identities"
    unique_together = (("provider", "provider_user_id"), ("user", "provider"))


class EmailVerification(models.Model):
  id = models.AutoField(primary_key=True)
  email = models.EmailField(unique=True)
  code = models.CharField(max_length=16)
  expires_at = models.DateTimeField(null=True, blank=True)
  verified_at = models.DateTimeField(null=True, blank=True)
  created_at = models.DateTimeField(auto_now_add=True)

  class Meta:
    db_table = "email_verifications"
