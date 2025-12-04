from datetime import timedelta
import secrets
import string
import json

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .email_utils import send_verification_code, verify_code
from .google_oauth import GoogleOAuthError, exchange_code_for_tokens, fetch_userinfo
from .jwt_utils import create_access_token

from .interview_utils import get_cached_graph, get_cached_llm
from tts_client import generate_interview_audio_batch

from .models import (
    AuthIdentity,
    CodingProblem,
    CodingProblemLanguage,
    TestCase,
    User,
)
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



class RandomCodingProblemView(APIView):
    """
    coding_problem + coding_problem_language 조합에서 언어별 랜덤 문제를 반환합니다.
    기본 언어는 python 입니다.
    """

    def get(self, request):
        language = (request.query_params.get("language") or "python").lower()
        problem_lang = (
            CodingProblemLanguage.objects.select_related("problem")
            .prefetch_related("problem__test_cases")
            .filter(language__iexact=language)
            .order_by("?")
            .first()
        )

        if not problem_lang:
            return Response(
                {"detail": f"요청한 언어({language})의 문제를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        problem = problem_lang.problem
        test_cases = [
            {"id": tc.id, "input": tc.input_data, "output": tc.output_data}
            for tc in (problem.test_cases.all() if hasattr(problem, "test_cases") else [])
        ]

        return Response(
            {
                "problem_id": problem.problem_id,
                "problem": problem.problem,
                "difficulty": problem.difficulty,
                "category": problem.category,
                "language": problem_lang.language,
                "function_name": problem_lang.function_name,
                "starter_code": problem_lang.starter_code,
                "test_cases": test_cases,
            }
        )


class CodingProblemSessionInitView(APIView):
    """
    RandomCodingProblemView 결과를 langgraph 초기 state에 넣어 실행한 뒤 상태를 반환합니다.
    - 프론트에서 RandomCodingProblemView 응답 전체를 POST 바디로 전달하면 DB 조회 없이 그대로 사용합니다.
    """

    def post(self, request):
        payload = request.data or {}
        # request.data가 문자열이면 JSON 파싱 시도
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        # RandomCodingProblemView 응답 전체를 그대로 보내면 problem 키 없이도 동작하도록 처리
        problem_data = payload.get("problem") if isinstance(payload, dict) else None
        if not problem_data and isinstance(payload, dict):
            problem_data = payload


        # langgraph 실행
        init_state = {
            "event_type": "init",
            "problem_data": problem_data,
            "await_human": False,
        }

        intro_text = None
        intro_audio = None
        graph_state = None
        graph_error = None
        tts_error = None

        try:
            graph = get_cached_graph()
            graph_state = graph.invoke(init_state)
            if isinstance(graph_state, dict):
                intro_text = graph_state.get("tts_text")
        except Exception as exc:  # noqa: BLE001
            graph_error = str(exc)

        # TTS 실행
        if intro_text:
            try:
                tts_result = generate_interview_audio_batch(intro_text)
                intro_audio = tts_result.get("audio_chunks")
            except Exception as exc:  # noqa: BLE001
                tts_error = str(exc)

        return Response(
            {
                "problem": problem_data,
                "intro_text": intro_text,
                "intro_audio": intro_audio,
                "graph_state": graph_state,
                "graph_error": graph_error,
                "tts_error": tts_error,
            },
            status=status.HTTP_200_OK,
        )


class WarmupLanggraphView(APIView):
    """
    Langgraph/LLM 모듈을 미리 로드하기 위한 워밍업 엔드포인트.
    """

    def get(self, request):
        try:
            # LLM 모듈 import 및 그래프 컴파일 시도
            llm_instance = get_cached_llm()
            graph = get_cached_graph()
            # LLM은 import 시점에 초기화되므로 존재만 확인
            _ = llm_instance
            graph.get_graph()  # 실제 실행은 하지 않고 DAG만 준비
            return Response({"status": "warmed"}, status=status.HTTP_200_OK)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"status": "error", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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


class UserIdCheckView(APIView):
    """
    아이디 중복 여부를 확인하는 엔드포인트.
    GET /api/auth/user-id/check/?user_id=some_id

    Response:
      200 OK: {"user_id": "...", "available": true/false}
      400 BAD REQUEST: {"detail": "..."} (user_id 미입력 등)
    """

    def get(self, request):
        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response(
                {"detail": "user_id를 쿼리스트링으로 전달해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        exists = User.objects.filter(user_id=user_id).exists()
        return Response({"user_id": user_id, "available": not exists})


class LoginView(APIView):
    def post(self, request):
        identifier = request.data.get("user_id") or request.data.get("email")
        password = request.data.get("password")

        if not identifier or not password:
            return Response(
                {"detail": "아이디(또는 이메일)와 비밀번호를 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(user_id=identifier).first()
        if not user:
            user = User.objects.filter(email=identifier).first()

        if not user or not user.password_hash or not check_password(password, user.password_hash):
            return Response(
                {"detail": "아이디 또는 비밀번호가 올바르지 않습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        access_token = create_access_token(user)

        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "access_token": access_token,
                "token_type": "bearer",
            },
            status=status.HTTP_200_OK,
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


class FindIdView(APIView):
    """
    이메일을 기준으로 user_id를 찾는 간단한 엔드포인트.
    실제 서비스에서는 보안상 이메일 발송 방식으로 변경하는 것이 좋습니다.
    """

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "이메일을 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(email=email).first()
        if not user:
            return Response({"detail": "해당 이메일로 가입된 아이디가 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 구글 소셜 로그인 계정은 아이디 찾기 대상에서 제외
        if AuthIdentity.objects.filter(user=user, provider="google").exists():
            return Response(
                {
                    "detail": "구글 소셜 로그인으로 가입한 계정은 아이디 찾기 기능을 사용할 수 없습니다. "
                    "구글 로그인을 이용해 주세요."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response({"email": email, "user_id": user.user_id})


class FindPasswordView(APIView):
    """
    이름, 아이디, 이메일을 기준으로 사용자를 찾고
    임시 비밀번호를 이메일로 발송한 뒤 해당 비밀번호로 갱신합니다.
    """

    def post(self, request):
        name = request.data.get("name")
        user_id = request.data.get("user_id")
        email = request.data.get("email")

        if not name or not user_id or not email:
            return Response(
                {"detail": "이름, 아이디, 이메일을 모두 입력해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user = User.objects.filter(user_id=user_id, email=email, name=name).first()
        if not user:
            return Response(
                {"detail": "입력하신 정보와 일치하는 계정을 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 구글 소셜 로그인 계정은 비밀번호 찾기/임시 비밀번호 발송 대상에서 제외
        if AuthIdentity.objects.filter(user=user, provider="google").exists():
            return Response(
                {
                    "detail": "구글 소셜 로그인으로 가입한 계정은 비밀번호 찾기 기능을 사용할 수 없습니다. "
                    "구글 로그인을 이용해 주세요."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 임시 비밀번호 생성
        alphabet = string.ascii_letters + string.digits
        temp_password = "".join(secrets.choice(alphabet) for _ in range(10))

        # 비밀번호 갱신
        user.password_hash = make_password(temp_password)
        user.updated_at = timezone.now()
        user.save(update_fields=["password_hash", "updated_at"])

        # 이메일 발송
        subject = "[JobTory] 임시 비밀번호 안내"
        message = (
            f"{user.name}님, 안녕하세요.\n\n"
            f"요청하신 임시 비밀번호는 아래와 같습니다.\n\n"
            f"임시 비밀번호: {temp_password}\n\n"
            "로그인 후 마이페이지에서 비밀번호를 꼭 변경해 주세요.\n"
        )
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
        except Exception:
            # 이메일 전송 실패 시에도 보안을 위해 구체적인 이유는 숨깁니다.
            return Response(
                {"detail": "임시 비밀번호 이메일 발송 중 오류가 발생했습니다."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {"detail": "임시 비밀번호를 이메일로 발송했습니다. 메일을 확인해 주세요."},
            status=status.HTTP_200_OK,
        )


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
        name = userinfo.get("name") or userinfo.get("given_name")

        expires_in = token_data.get("expires_in")
        refresh_token = token_data.get("refresh_token")

        auth_identity = (
            AuthIdentity.objects.filter(provider="google", provider_user_id=sub)
            .select_related("user")
            .first()
        )
        if auth_identity:
            user = auth_identity.user
            # 새로 받은 토큰 정보가 있으면 갱신
            fields_to_update = []
            if refresh_token:
                auth_identity.refresh_token = refresh_token
                fields_to_update.append("refresh_token")
            if expires_in:
                auth_identity.token_expires_at = timezone.now() + timedelta(seconds=int(expires_in))
                fields_to_update.append("token_expires_at")
            if fields_to_update:
                auth_identity.save(update_fields=fields_to_update)
        else:
            # 기존 이메일로 유저 있으면 연결, 없으면 생성
            user = User.objects.filter(email=email).first()
            if not user:
                # 소셜 전용 계정은 이메일을 PK로 사용, 이메일이 없으면 sub를 사용
                user_pk = email or sub
                user = User.objects.create(
                    user_id=user_pk,
                    email=email,
                    name=name,
                    password_hash=None,
                    phone_number=None,
                    birthdate=None,
                    created_at=timezone.now(),
                    updated_at=timezone.now(),
                )
            expires_at = (
                timezone.now() + timedelta(seconds=int(expires_in))
                if expires_in is not None
                else None
            )
            AuthIdentity.objects.create(
                user=user,
                provider="google",
                provider_user_id=sub,
                refresh_token=refresh_token,
                token_expires_at=expires_at,
                created_at=timezone.now(),
            )

        access_token = create_access_token(user)

        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "provider": "google",
                "access_token": access_token,
                "token_type": "bearer",
            }
        )
