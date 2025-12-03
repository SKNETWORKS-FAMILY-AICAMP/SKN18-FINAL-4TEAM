from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from .analyzer import analyze_frame


class CheatAnalysisView(APIView):
    """
    mediapipe를 사용해 단일 이미지 프레임에서 부정행위 여부를 분석하는 엔드포인트.
    - 입력: multipart/form-data, field name: "image"
    - 출력: { is_cheating, reason, face_count, raw_score }
    """

    parser_classes = (MultiPartParser, FormParser)

    def post(self, request):
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

        return Response(result.to_dict(), status=status.HTTP_200_OK)
