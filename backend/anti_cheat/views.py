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

from .analyzer import analyze_frame


class CheatAnalysisView(APIView):
    """
    mediapipe를 사용해 단일 이미지 프레임에서 부정행위 여부를 분석하는 엔드포인트.
    - 입력: multipart/form-data, field name: "image"
    - 출력: { is_cheating, reason, face_count, raw_score }
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
            try:
                if data.get("is_cheating"):
                    cache_key = f"anti:mediapipe:{session_id}:cheat_count"
                    cache.incr(cache_key)
                    cache.expire(cache_key, 60 * 60)
                    # 최근 사유 로그를 남깁니다(최대 20건).
                    reasons_key = f"anti:mediapipe:{session_id}:reasons"
                    cache.lpush(
                        reasons_key,
                        json.dumps(
                            {
                                "ts": time.time(),
                                "reason": data.get("reason"),
                                "raw_score": data.get("raw_score"),
                            }
                        ),
                    )
                    cache.ltrim(reasons_key, 0, 19)
                    cache.expire(reasons_key, 60 * 60)
            except Exception:
                # 모니터링 용도이므로 카운터 기록 실패는 전체 요청 실패로 만들지 않습니다.
                pass

        return Response(data, status=status.HTTP_200_OK)


def _face_count_from_bytes(image_bytes: bytes) -> int:
    """
    빠른 얼굴 존재 확인용 헬퍼: mediapipe FaceDetection으로 face_count만 계산.
    """
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise ValueError("이미지를 디코딩할 수 없습니다.")

    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    with mp.solutions.face_detection.FaceDetection(
        model_selection=0, min_detection_confidence=0.5
    ) as detector:
        result = detector.process(img_rgb)
    if not result.detections:
        return 0
    return len(result.detections)


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
