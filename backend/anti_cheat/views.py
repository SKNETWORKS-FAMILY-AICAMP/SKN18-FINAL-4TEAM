import json
import time

import cv2
import mediapipe as mp
import numpy as np
from django.core.cache import cache
from rest_framework import permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .analyzer import analyze_frame, _face_count_from_bytes


class CheatAnalysisView(APIView):
    """
    mediapipe를 사용해 단일 이미지 프레임에서 부정행위 여부를 분석하는 엔드포인트.
    - 입력: multipart/form-data, field name: "image"
    - 출력: { is_cheating, reason}
    """

    permission_classes = [permissions.AllowAny]
    # 이 엔드포인트는 5초마다 호출되므로 전역 DRF throttling에서 제외합니다.
    throttle_classes: list = []
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        session_id = request.query_params.get("session_id")
        file = request.FILES.get("image")
        if not file:
            return Response(
                {"detail": "image 파일을 multipart/form-data로 전송해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = analyze_frame(file.read())
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "이미지 분석 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        data = result.to_dict()

        # 세션 ID가 있으면 간단한 부정행위 카운터를 Redis(캐시)에 기록합니다.
        if session_id:
            base_key = f"livecoding:{session_id}:anti-cheat"

            if data.get("is_cheating"):
                # base_key 하나에 dict 형태로 누적 저장
                cache_data = cache.get(base_key) or {}
                cheat_count = int(cache_data.get("cheat_count", 0)) + 1
                reasons = cache_data.get("reasons", [])
                if not isinstance(reasons, list):
                    reasons = []
                reasons.append(
                    {
                        "ts": time.time(),
                        "cheat_reason": data.get("detail_reason"),
                    }
                )
                cache.set(
                    base_key,
                    {"cheat_count": cheat_count, "reasons": reasons},
                    timeout=60 * 60,
                )
   

        return Response(data, status=status.HTTP_200_OK)

class FacePresenceView(APIView):
    """
    설정 페이지용 경량 얼굴 존재 확인 엔드포인트.
    - 입력: multipart/form-data, field name: "image"
    - 출력: { face_count, face_visible: bool }
    """

    permission_classes = [permissions.AllowAny]
    throttle_classes: list = []
    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
        file = request.FILES.get("image")
        if not file:
            return Response(
                {"detail": "image 파일을 multipart/form-data로 전송해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            count = _face_count_from_bytes(file.read())
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response(
                {"detail": "얼굴 감지 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"face_count": count, "face_visible": count > 0},
            status=status.HTTP_200_OK,
        )
