from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .email_utils import send_verification_code, verify_code
from .google_oauth import GoogleOAuthError, exchange_code_for_tokens, fetch_userinfo
from .models import AuthIdentity, User
from .serializers import SignupSerializer


def health(request):
    return JsonResponse({"status": "ok"})


def roadmap(request):
    data = {
        "phases": [
            {
                "name": "pre_interview",
                "steps": [
                    "문항/자기소개서 기반 분석",
                    "JD 기반 질문 생성",
                    "세션 시작 및 환경 확인",
                ],
            },
            {
                "name": "behavioral_interview",
                "steps": [
                    "상황 질문 4~5개",
                    "STT/TTS, 시선/표정 추적",
                    "평가 리포트 생성",
                ],
            },
            {
                "name": "coding_test",
                "steps": [
                    "문제 1~4 세트",
                    "코드 자동 채점 및 리포트",
                ],
            },
        ]
    }
    return JsonResponse(data)


class SignupView(APIView):
    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "birthdate": user.birthdate,
            },
            status=status.HTTP_201_CREATED,
        )


class EmailSendView(APIView):
    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "이메일을 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        code, expires_at = send_verification_code(email)
        return Response({"email": email, "expires_at": expires_at})


class EmailVerifyView(APIView):
    def post(self, request):
        email = request.data.get("email")
        code = request.data.get("code")
        if not email or not code:
            return Response({"detail": "이메일과 인증코드를 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        ok, msg = verify_code(email, code)
        if not ok:
            return Response({"detail": msg}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"email": email, "verified": True, "message": msg})


class GoogleAuthView(APIView):
    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "code가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        redirect_uri = settings.GOOGLE_REDIRECT_URI
        try:
            token_data = exchange_code_for_tokens(code, redirect_uri)
            userinfo = fetch_userinfo(token_data["access_token"])
        except GoogleOAuthError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        sub = userinfo["sub"]
        email = userinfo.get("email")
        name = userinfo.get("name") or "Google User"

        auth_identity = AuthIdentity.objects.filter(provider="google", provider_user_id=sub).select_related("user").first()
        if auth_identity:
            user = auth_identity.user
        else:
            # 기존 이메일로 유저 있으면 연결, 없으면 생성
            user = User.objects.filter(email=email).first()
            if not user:
                user = User.objects.create(
                    email=email,
                    name=name,
                    password_hash=None,
                    phone_number=None,
                    birthdate=None,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
            AuthIdentity.objects.create(
                user=user,
                provider="google",
                provider_user_id=sub,
                created_at=timezone.now(),
            )

        # TODO: JWT 발급 로직 연결 (지금은 user 데이터만 반환)
        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "provider": "google",
            }
        )