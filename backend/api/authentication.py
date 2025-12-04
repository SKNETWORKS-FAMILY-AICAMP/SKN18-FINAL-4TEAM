from __future__ import annotations

from typing import Any, Tuple

import jwt
from django.conf import settings
from rest_framework import authentication, exceptions

from .models import User


class JWTAuthentication(authentication.BaseAuthentication):
    """
    간단한 Bearer JWT 인증 클래스.
    - Authorization: Bearer <access_token>
    - payload.sub를 user_id로 사용해 User를 조회합니다.
    """

    keyword = "Bearer"

    def authenticate(self, request) -> Tuple[User, Any] | None:
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            return None

        parts = auth_header.split()
        if len(parts) != 2 or parts[0] != self.keyword:
            # 다른 인증 스킴이면 JWT로는 처리하지 않고 패스
            return None

        token = parts[1].strip()
        if not token:
            raise exceptions.AuthenticationFailed("인증 토큰이 비어 있습니다.")

        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed("토큰이 만료되었습니다.")
        except jwt.PyJWTError:
            raise exceptions.AuthenticationFailed("유효하지 않은 인증 토큰입니다.")

        user_id = payload.get("sub")
        if not user_id:
            raise exceptions.AuthenticationFailed("토큰에 사용자 정보가 없습니다.")

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise exceptions.AuthenticationFailed("사용자를 찾을 수 없습니다.")

        # request.user, request.auth 로 전달됩니다.
        return user, payload

