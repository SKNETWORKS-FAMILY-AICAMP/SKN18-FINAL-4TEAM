import random
import string
from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.utils import timezone

from .models import EmailVerification


def generate_code(length=6):
    return "".join(random.choices(string.digits, k=length))


def send_verification_code(email: str):
    code = generate_code()
    now = timezone.now()
    expires_at = now + timedelta(minutes=10)

    EmailVerification.objects.update_or_create(
        email=email,
        defaults={"code": code, "expires_at": expires_at, "verified_at": None, "created_at": now},
    )

    subject = "[JobTory] 이메일 인증 코드"
    message = f"아래 인증 코드를 10분 이내에 입력해 주세요.\n\n코드: {code}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email], fail_silently=False)
    return code, expires_at


def verify_code(email: str, code: str):
    try:
        record = EmailVerification.objects.get(email=email, code=code)
    except EmailVerification.DoesNotExist:
        return False, "인증 코드가 올바르지 않습니다."

    if record.expires_at and record.expires_at < timezone.now():
        return False, "인증 코드가 만료되었습니다."

    record.verified_at = timezone.now()
    record.save(update_fields=["verified_at"])
    return True, "인증 완료"
