from __future__ import annotations

from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(UserRateThrottle):
    scope = "login"


class PasswordResetRateThrottle(UserRateThrottle):
    scope = "password_reset"


class EmailActionRateThrottle(UserRateThrottle):
    scope = "email"


class AnonStrictRateThrottle(AnonRateThrottle):
    """
    필요시 익명 사용자에 대해 더 엄격한 레이트 리밋을 적용할 때 사용할 수 있는 스코프입니다.
    """

    scope = "anon_strict"

