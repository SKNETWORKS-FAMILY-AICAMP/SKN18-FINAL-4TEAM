from django.core.cache import cache
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import JWTAuthentication
from .models import User


class LiveCodingTimerUpdateView(APIView):
    """
    라이브 코딩 세션 타이머(remaining_seconds)를 갱신하는 엔드포인트.
    - Authorization: Bearer <access_token>
    - POST /api/livecoding/session/timer/
      body: { "session_id": "...", "remaining_seconds": 1234 }

    화면을 떠날 때 현재 남은 시간을 저장해 두고,
    이후 이어하기 진입 시 이 값을 기준으로 다시 카운트다운을 시작하기 위해 사용한다.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "타이머를 업데이트하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = request.data or {}
        session_id = data.get("session_id")
        remaining = data.get("remaining_seconds")

        if not session_id:
            return Response(
                {"detail": "session_id가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            remaining_val = int(remaining)
        except (TypeError, ValueError):
            return Response(
                {"detail": "remaining_seconds는 정수여야 합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key) or {}
        if not meta:
            return Response(
                {"detail": "세션 메타 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 메타에 저장된 user_id와 현재 로그인 유저가 일치하는지 검증
        if str(meta.get("user_id")) != str(user.user_id):
            return Response(
                {"detail": "이 세션의 타이머를 업데이트할 수 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        time_limit_seconds = int(meta.get("time_limit_seconds") or 40 * 60)
        remaining_clamped = max(0, min(time_limit_seconds, remaining_val))
        meta["remaining_seconds"] = remaining_clamped

        cache.set(meta_key, meta, timeout=60 * 60)

        return Response(
            {"remaining_seconds": remaining_clamped},
            status=status.HTTP_200_OK,
        )
