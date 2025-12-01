from django.contrib.auth.hashers import make_password
from django.utils import timezone
from rest_framework import serializers

from .models import AuthIdentity, EmailVerification, User


class SignupSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8, max_length=128)
    name = serializers.CharField(max_length=50)
    phone_number = serializers.CharField(
        required=False, allow_blank=True, allow_null=True, max_length=30
    )
    birthdate = serializers.DateField(required=False, allow_null=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("이미 사용 중인 이메일입니다.")
        if EmailVerification.objects.filter(email=value, verified_at__isnull=False).exists() is False:
            raise serializers.ValidationError("이메일 인증을 완료해 주세요.")
        return value

    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exists():
            raise serializers.ValidationError("이미 사용 중인 전화번호입니다.")
        return value

    def create(self, validated_data):
        now = timezone.now()
        password = validated_data.pop("password", None)
        hashed_pw = make_password(password) if password else None

        user = User.objects.create(
            password_hash=hashed_pw,
            created_at=now,
            updated_at=now,
            **validated_data,
        )

        # 로컬 로그인 자격 연결
        AuthIdentity.objects.create(
            user=user,
            provider="local",
            provider_user_id=user.email,
            created_at=now,
        )

        return user
