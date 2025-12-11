from datetime import datetime, timedelta, date
import json
import secrets
import string
import time

from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.utils import timezone
from django.contrib.auth.hashers import check_password, make_password
from django.core.cache import cache
from rest_framework import status, permissions
import jwt
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny

from .email_utils import send_verification_code, verify_code
from .throttling import (
    EmailActionRateThrottle,
    LoginRateThrottle,
    PasswordResetRateThrottle,
)
from .stt_buffer import clear_utterances
from .google_oauth import GoogleOAuthError, exchange_code_for_tokens, fetch_userinfo
from .jwt_utils import create_access_token

from .interview_utils import get_cached_graph, get_cached_llm, _generate_tts_payload

from .models import (
    AuthIdentity,
    CodingProblem,
    CodingProblemLanguage,
    TestCase,
    User,
)
from .serializers import SignupSerializer
from .authentication import JWTAuthentication


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

    permission_classes = [permissions.AllowAny]

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


class CodingProblemTextInitView(APIView):
    """
    RandomCodingProblemView 응답을 받아 LangGraph 초기 상태만 실행하고,
    문제 텍스트와 인트로용 tts_text(텍스트만)를 반환하는 경량 엔드포인트.

    - POST /api/coding-problems/session/init/?session_id=...:
      body: RandomCodingProblemView 응답 전체(JSON)
      response: {"problem": "...", "tts_text": "..."}
    """

    def post(self, request):
        payload = request.data or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}

        if not isinstance(payload, dict):
            payload = {}

        problem_text = ""
        if isinstance(payload.get("problem"), str):
            problem_text = payload["problem"]
            
        session_id = (
            request.query_params.get("session_id")
            or request.headers.get("X-Session-Id")
            or (request.data.get("session_id") if hasattr(request, "data") else None)
        )
        if not session_id:
            return Response(
                {"detail": "session_id 쿼리 파라미터를 전달해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        init_state = {
            "meta": {
                "session_id": session_id,
                "user_id": request.user.user_id if hasattr(request, "user") else None,
            },
            "event_type": "init",
            "problem_data": problem_text,
            "intro_flow_done": False,
        }

        intro_text = ""
        try:
            graph = get_cached_graph(session_id=session_id, name ="chapter1")
            graph_state = graph.invoke(
                init_state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_namespace":"chapter1"
                    }
                },
            )
            if isinstance(graph_state, dict):
                intro_text = graph_state.get("tts_text") or ""
        except Exception as exc:  # noqa: BLE001
            return Response(
                {
                    "detail": "langgraph 호출을 할 수 없습니다.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "tts_text": intro_text,
            },
            status=status.HTTP_200_OK,
        )


class TTSView(APIView):
    """
    텍스트를 받아 TTS만 수행하는 엔드포인트.
    - POST /api/tts/intro/?session_id=...
      body: {"tts_text": "..."} 또는 {"text": "..."}
      response: CodingProblemSessionInitView와 동일한 오디오 청크 구조
    """

    def post(self, request):
        data = request.data or {}
        text = (data.get("tts_text") or data.get("text") or "").strip()
        max_sentences = data.get("max_sentences")

        if not text:
            return Response(
                {"detail": "tts_text(또는 text) 필드를 전달해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_id = (
            request.query_params.get("session_id")
            or request.headers.get("X-Session-Id")
            or (request.data.get("session_id") if hasattr(request, "data") else None)
        )

        try:
            sentences_payload = _generate_tts_payload(text, session_id, max_sentences)
        except Exception as exc:  # noqa: BLE001
            return Response(
                {
                    "detail": "TTS 함수를 실행할 수 없습니다.",
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "tts_text": sentences_payload
            },
            status=status.HTTP_200_OK,
        )


class WarmupLanggraphView(APIView):
    """
    Langgraph/LLM 모듈을 미리 로드하기 위한 워밍업 엔드포인트.
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def get(self, request):
        try:
            # LLM 모듈 import 및 그래프 컴파일 시도
            llm_instance = get_cached_llm()
            _ = llm_instance   # LLM은 존재 확인
            
            # 쿼리/헤더/바디 어디서든 session_id를 받되, 없으면 400 반환
            data = request.data if hasattr(request, "data") else {}
            session_id = None
            if isinstance(data, dict):
                session_id = data.get("session_id")
            session_id = (
                session_id
                or request.query_params.get("session_id")
                or request.headers.get("X-Session-Id")
            )
            
            if not session_id: # session_id 업을 때 예외 처리
                return Response(
                    {"detail": "session_id가 필요합니다."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
                
        
            graph1 = get_cached_graph(session_id=session_id, name="chapter1")
            graph1.get_graph()  # 실제 실행은 하지 않고 DAG만 준비
            return Response({"status": "warmed"}, status=status.HTTP_200_OK)
        
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"status": "error", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InterviewIntroEventView(APIView):
    """
    STT로 얻은 텍스트를 기반으로 LangGraph 호출하여,
    다음 질문/피드백/단계 정보를 반환하는 엔드포인트.

    - POST /api/interview/event/
      body: {
        "session_id": "...",
        "stt_text": "...",
        "event_type": "strategy_submit" | "init"
    """

    def post(self, request):
        data = request.data or {}
        session_id = (
            data.get("session_id")
            or request.query_params.get("session_id")
            or request.headers.get("X-Session-Id")
        )
        stt_text = (data.get("stt_text") or "").strip()
        event_type = "strategy_submit"

        if not session_id:
            return Response(
                {"detail": "session_id를 body, 쿼리스트링 또는 X-Session-Id 헤더로 전달해 주세요."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not stt_text:
            return Response(
                {"detail": "stt_text 필드를 비울 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 현재 세션 stage 확인 (meta 기준)
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key) or {}
        current_stage = meta.get("stage") or "intro"

        # 코딩 단계에서는 chapter2 그래프의 답변 리액션 노드만 호출해
        # 짧은 피드백 멘트를 생성한다.
        if current_stage == "coding":
            try:
                coding_graph = get_cached_graph(session_id=session_id, name="chapter2")
                coding_state = {
                    "meta": {
                        "session_id": session_id,
                        "user_id": getattr(request.user, "user_id", None),
                    },
                    "event_type": "question_answer",
                    "stt_text": stt_text,
                }
                coding_result = coding_graph.invoke(
                    coding_state,
                    config={
                        "configurable": {
                            "thread_id": session_id,
                            "checkpoint_namespace": "chapter2",
                        }
                    },
                )
                reply_tts = (coding_result.get("tts_text") or "").strip()
            except Exception:
                # LangGraph 호출 실패 시에도 기본 멘트로 폴백
                reply_tts = (
                    "답변 잘 들었습니다. 이제 다시 문제 풀이를 이어가 주세요."
                )

            return Response(
                {
                    "stt_text": stt_text,
                    "tts_text": reply_tts,
                    "user_question": None,
                    "problem_answer": None,
                    "user_answer_class": None,
                    "intro_flow_done": False,
                    "stage": "coding",
                    "coding_intro_text": "",
                },
                status=status.HTTP_200_OK,
            )

        graph = get_cached_graph(session_id=session_id, name="chapter1")

        update_state = {
            "event_type": event_type,
            "stt_text": stt_text,
        }

        try:
            result_state = graph.invoke(
                update_state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_namespace": "chapter1",
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"error": "langgraph invoke failed", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # LangGraph가 내려준 TTS 텍스트
        tts_text = (result_state.get("tts_text") or "").strip()

        # TTS는 별도 엔드포인트(TTSView)에서 호출하도록 분리
        user_answer_class = (result_state.get("user_answer_class") or "").strip() or None

        # stage는 meta 기준으로 결정 (intro -> coding 단방향)
        stage = meta.get("stage") or "intro"
        coding_intro_text = ""
        if user_answer_class == "strategy":
            # 1) stage 전환
            stage = "coding"
            meta["stage"] = "coding"
            cache.set(meta_key, meta, timeout=60 * 60)

            # 2) 코딩 스테이지 인트로: chapter2 그래프 내 coding_intro 노드만 실행
            try:
                coding_graph = get_cached_graph(session_id=session_id, name="chapter2")
                coding_state = {
                    "meta": {
                        "session_id": session_id,
                        "user_id": getattr(request.user, "user_id", None),
                    },
                    "event_type": "coding_intro",
                    # 언어 정보가 메타에 있다면 넘겨주고, 없으면 python 기본값
                    "language": (meta.get("language") or "python"),
                }
                coding_result = coding_graph.invoke(
                    coding_state,
                    config={
                        "configurable": {
                            "thread_id": session_id,
                            "checkpoint_namespace": "chapter2",
                        }
                    },
                )
                coding_intro_text = (coding_result.get("tts_text") or "").strip()
            except Exception as exc:
                # LangGraph 쪽에서 문제가 나더라도 코딩 인트로 멘트는 반드시 한 번 재생되도록
                # 간단한 폴백 멘트를 설정해 둔다.
                coding_intro_text = (
                    "좋습니다. 이제 코딩 테스트를 시작하겠습니다. "
                    "너무 긴장하지 마시고, 평소 하시던 방식대로 차분히 코드를 작성해 주세요."
                )

        # 코딩 스테이지로 전환되면서 추가 멘트가 있다면 기존 TTS 텍스트 뒤에 붙인다.
        if coding_intro_text:
            if tts_text:
                tts_text = f"{tts_text}\n\n{coding_intro_text}"
            else:
                tts_text = coding_intro_text

        response_payload = {
            "stt_text": stt_text,
            "tts_text": tts_text,
            "user_question": result_state.get("user_question"),
            "problem_answer": result_state.get("problem_answer"),
            "user_answer_class": user_answer_class,
            "intro_flow_done": result_state.get("intro_flow_done"),
            "stage": stage,
            # 코딩 스테이지로 막 전환될 때만 설정되는 인트로 멘트 텍스트
            "coding_intro_text": coding_intro_text or "",
        }

        return Response(response_payload, status=status.HTTP_200_OK)


class SignupView(APIView):
    permission_classes = [permissions.AllowAny]

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

    permission_classes = [permissions.AllowAny]

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
    permission_classes = [permissions.AllowAny]
    throttle_classes = [LoginRateThrottle]

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


class UserMeView(APIView):
    """
    단순 JWT 검증 후 사용자 프로필 반환.
    """

    def get(self, request):
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.lower().startswith("bearer "):
            return Response({"detail": "인증 정보가 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(" ", 1)[1].strip()
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        except jwt.ExpiredSignatureError:
            return Response({"detail": "토큰이 만료되었습니다."}, status=status.HTTP_401_UNAUTHORIZED)
        except jwt.InvalidTokenError:
            return Response({"detail": "유효하지 않은 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        user_id = payload.get("sub")
        if not user_id:
            return Response({"detail": "유효하지 않은 토큰입니다."}, status=status.HTTP_401_UNAUTHORIZED)

        user = User.objects.filter(user_id=user_id).first()
        if not user:
            return Response({"detail": "사용자를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "birthdate": user.birthdate,
            },
            status=status.HTTP_200_OK,
        )


class LogoutView(APIView):
    """
    클라이언트 측 토큰 제거용 엔드포인트 (서버 상태 없음).
    """

    def post(self, request):
        return Response({"detail": "logged_out"}, status=status.HTTP_200_OK)


class EmailSendView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_classes = [EmailActionRateThrottle]

    def post(self, request):
        email = request.data.get("email")
        if not email:
            return Response({"detail": "이메일을 입력해 주세요."}, status=status.HTTP_400_BAD_REQUEST)
        code, expires_at = send_verification_code(email)
        return Response({"email": email, "expires_at": expires_at})


class EmailVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

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

    permission_classes = [permissions.AllowAny]
    throttle_classes = [EmailActionRateThrottle]

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

    permission_classes = [permissions.AllowAny]
    throttle_classes = [PasswordResetRateThrottle]

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
    permission_classes = [permissions.AllowAny]

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


class LiveCodingStartView(APIView):
    """
    라이브 코딩 세션을 시작하면서 세션 메타 정보를 저장하는 엔드포인트.
    - Authorization: Bearer <access_token> (LoginView/GoogleAuthView에서 발급한 토큰)
    - 요청 본문(optional): {"language": "python"} 등
    - 저장되는 키: livecoding:{session_id}:meta
      값: { state, problem_id, user_id, session_id }
    """

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "라이브 코딩을 시작하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        language = (request.data.get("language") or "python").lower()
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
        session_id = secrets.token_hex(16)

        test_cases = [
            {"id": tc.id, "input": tc.input_data, "output": tc.output_data}
            for tc in (problem.test_cases.all() if hasattr(problem, "test_cases") else [])
        ]

        # Redis(캐시)에 저장할 세션 메타 정보
        start_at = timezone.now()
        meta = {
            "state": "in_progress",
            "problem_id": problem.problem_id,
            "user_id": user.user_id,
            "session_id": session_id,
            "language": problem_lang.language,
            # starter_code를 메타에도 보관해 두어, 이후 코드 진행 여부 판단에 사용
            "starter_code": problem_lang.starter_code,
            "time_limit_seconds": 40 * 60,
            "start_at": start_at.isoformat(),
        }

        # 기본 TTL: 1시간 (필요 시 환경변수로 조정 가능)
        cache.set(f"livecoding:{session_id}:meta", meta, timeout=60 * 60)
        # 유저별 현재 진행 중인 세션 매핑
        cache.set(
            f"livecoding:user:{user.user_id}:current_session",
            session_id,
            timeout=60 * 60,
        )

        return Response(
            {
                "session_id": session_id,
                "state": meta["state"],
                "user_id": meta["user_id"],
                "problem_id": meta["problem_id"],
                "problem": problem.problem,
                "difficulty": problem.difficulty,
                "category": problem.category,
                "language": problem_lang.language,
                "function_name": problem_lang.function_name,
                "starter_code": problem_lang.starter_code,
                "test_cases": test_cases,
                "time_limit_seconds": meta["time_limit_seconds"],
                "start_at": meta["start_at"],
                "remaining_seconds": meta["time_limit_seconds"],
            },
            status=status.HTTP_201_CREATED,
        )


class LiveCodingCodeSnapshotView(APIView):
    """
    라이브 코딩 세션 중 작성 중인 코드를 Redis(cache)에 지속적으로 저장/조회하는 엔드포인트.
    - POST: 코드 스냅샷 저장
      body: { "session_id": "...", "language": "python3", "code": "..." }
    - GET: 마지막(또는 언어별 마지막) 코드 스냅샷 조회
      query: ?session_id=...&language=python3 (language는 선택)
    """

    def _get_and_validate_meta(self, user, session_id: str):
        if not session_id:
            return None, Response(
                {"detail": "session_id가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key)
        if not meta:
            return None, Response(
                {"detail": "해당 세션 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if str(meta.get("user_id")) != str(getattr(user, "user_id", None)):
            return None, Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        return meta, None

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "코드를 저장하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_id = request.data.get("session_id")
        code = request.data.get("code")
        language = (request.data.get("language") or "").lower() or None

        if code is None:
            return Response(
                {"detail": "code 필드는 비워둘 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meta, error_response = self._get_and_validate_meta(user, session_id)
        if error_response is not None:
            return error_response

        # language가 명시되지 않은 경우 세션 메타의 언어를 사용
        if not language:
            language = (meta.get("language") or "").lower() or None

        snapshot = {
            "code": str(code),
            "language": language,
            "saved_at": timezone.now().isoformat(),
        }

        key = f"livecoding:{session_id}:code"
        data = cache.get(key) or {}
        history = data.get("history") or []
        history.append(snapshot)

        # 메모리 보호를 위해 최대 200개까지만 유지
        if len(history) > 200:
            history = history[-200:]

        data["latest"] = snapshot
        data["history"] = history

        # 세션 메타 TTL(기본 1시간)과 동일하게 유지
        cache.set(key, data, timeout=60 * 60)

        return Response(
            {"saved": True, "snapshot": snapshot},
            status=status.HTTP_201_CREATED,
        )

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "코드를 조회하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_id = request.query_params.get("session_id")
        requested_language = (request.query_params.get("language") or "").lower()

        meta, error_response = self._get_and_validate_meta(user, session_id)
        if error_response is not None:
            return error_response

        key = f"livecoding:{session_id}:code"
        data = cache.get(key)
        if not data:
            return Response(
                {"detail": "저장된 코드 스냅샷이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        history = data.get("history") or []
        latest = data.get("latest") or {}

        # 언어가 지정된 경우 해당 언어의 마지막 스냅샷을 우선적으로 반환
        snapshot = None
        if requested_language and history:
            for item in reversed(history):
                if (item.get("language") or "").lower() == requested_language:
                    snapshot = item
                    break

        if snapshot is None:
            snapshot = latest

        if not snapshot:
            return Response(
                {"detail": "저장된 코드 스냅샷이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response(
            {
                "session_id": session_id,
                "language": snapshot.get("language") or meta.get("language"),
                "code": snapshot.get("code") or "",
                "saved_at": snapshot.get("saved_at"),
            },
            status=status.HTTP_200_OK,
        )

class LiveCodingHintView(APIView):
    """
    라이브코딩 세션 중 힌트 요청을 LangGraph(챕터2)로 전달합니다.
    - Authorization: Bearer <access_token>
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "힌트 요청을 위해서는 로그인/인증이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        data = request.data or {}
        session_id = (
            data.get("session_id")
            or request.query_params.get("session_id")
            or request.headers.get("X-Session-Id")
        )
        if not session_id:
            return Response({"detail": "session_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key)
        if not meta:
            return Response({"detail": "해당 세션 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        if str(meta.get("user_id")) != str(user.user_id):
            return Response({"detail": "본인 세션에만 접근할 수 있습니다."}, status=status.HTTP_403_FORBIDDEN)

        language = (data.get("language") or meta.get("language") or "").lower() or None
        code = data.get("code") or ""
        user_algorithm_category = (
            data.get("problem_algorithm_category")
            or data.get("user_algorithm_category")
            or ""
        )
        real_algorithm_category = data.get("real_algorithm_category") or ""
        problem_description = data.get("problem_description") or ""
        hint_trigger = data.get("hint_trigger") or "manual"
        conversation_log = data.get("conversation_log") if isinstance(data.get("conversation_log"), list) else None
        hint_count_raw = data.get("hint_count")
        test_cases_payload = data.get("test_cases")

        try:
            hint_count = int(hint_count_raw) if hint_count_raw is not None else None
        except Exception:
            hint_count = None

        # 요청에 값이 없으면 로그에서 힌트 횟수를 추정
        if hint_count is None:
            if conversation_log:
                hint_count = sum(1 for entry in conversation_log if isinstance(entry, dict) and entry.get("type") == "hint")
            else:
                hint_count = 0

        problem_lang = None
        if meta.get("problem_id"):
            qs = (
                CodingProblemLanguage.objects.select_related("problem")
                .prefetch_related("problem__test_cases")
                .filter(problem__problem_id=meta.get("problem_id"))
            )
            if language:
                qs = qs.filter(language__iexact=language)
            problem_lang = qs.first()

        if problem_lang:
            problem_obj = problem_lang.problem
            if not problem_description:
                problem_description = problem_obj.problem or ""
            if not real_algorithm_category:
                real_algorithm_category = problem_obj.category or ""
            if not test_cases_payload:
                test_cases_payload = [
                    {"input": tc.input_data, "output": tc.output_data}
                    for tc in (problem_obj.test_cases.all() if hasattr(problem_obj, "test_cases") else [])
                ]

        test_cases_str = ""
        if isinstance(test_cases_payload, str):
            test_cases_str = test_cases_payload
        elif test_cases_payload is not None:
            try:
                test_cases_str = json.dumps(test_cases_payload, ensure_ascii=False)
            except Exception:
                test_cases_str = str(test_cases_payload)

        state = {
            "meta": {"session_id": session_id, "user_id": str(user.user_id)},
            "current_user_code": code,
            "problem_description": problem_description,
            "user_algorithm_category": user_algorithm_category,
            "real_algorithm_category": real_algorithm_category,
            "test_cases": test_cases_str,
            "hint_trigger": hint_trigger,
            "hint_count": hint_count,
        }
        if conversation_log is not None:
            state["conversation_log"] = conversation_log

        try:
            graph = get_cached_graph(session_id=session_id, name="chapter2")
            result_state = graph.invoke(
                state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_namespace": "chapter2",
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": "langgraph invoke failed", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        hint_text = (result_state.get("hint_text") or "").strip()
        tts_audio = []
        if hint_text:
            try:
                # 힌트를 바로 읽어줄 수 있도록 오디오 청크도 함께 반환
                tts_audio = _generate_tts_payload(hint_text, session_id, max_sentences=2)
            except Exception:
                tts_audio = []

        return Response(
            {
                "hint_text": hint_text,
                "hint_count": result_state.get("hint_count", hint_count),
                "conversation_log": result_state.get("conversation_log"),
                "hint_trigger": hint_trigger,
                "tts_audio": tts_audio,
            },
            status=status.HTTP_200_OK,
        )

class LiveCodingSessionView(APIView):
    """
    Redis에 저장된 라이브 코딩 세션 정보를 가져오는 엔드포인트.
    - Authorization: Bearer <access_token>
    - query: ?session_id=<sid>
    - 응답: LiveCodingStartView와 동일한 형태의 문제/세션 정보
    """

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "세션 정보를 조회하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "session_id 쿼리 파라미터가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        meta_key = f"livecoding:{session_id}:meta"

        meta = cache.get(meta_key)
        if not meta:
            return Response(
                {"detail": "해당 세션 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 다른 사용자의 세션에 접근하지 못하도록 검증
        if meta.get("user_id") != str(user.user_id):
            return Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        problem_id = meta.get("problem_id")
        language = meta.get("language")

        qs = (
            CodingProblemLanguage.objects.select_related("problem")
            .prefetch_related("problem__test_cases")
            .filter(problem__problem_id=problem_id)
        )
        if language:
            qs = qs.filter(language__iexact=language)

        problem_lang = qs.first()
        if not problem_lang:
            return Response(
                {"detail": "세션의 문제 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        problem = problem_lang.problem
        test_cases = [
            {"id": tc.id, "input": tc.input_data, "output": tc.output_data}
            for tc in (problem.test_cases.all() if hasattr(problem, "test_cases") else [])
        ]

        start_at_str = meta.get("start_at")
        time_limit_seconds = int(meta.get("time_limit_seconds") or 40 * 60)
        remaining_seconds = time_limit_seconds

        if start_at_str:
            try:
                start_at_dt = datetime.fromisoformat(start_at_str)
                if timezone.is_naive(start_at_dt):
                    start_at_dt = timezone.make_aware(start_at_dt, timezone=timezone.utc)
                elapsed = max(0, int((timezone.now() - start_at_dt).total_seconds()))
                remaining_seconds = max(0, time_limit_seconds - elapsed)
            except Exception:
                remaining_seconds = time_limit_seconds

        return Response(
            {
                "session_id": session_id,
                "state": meta.get("state"),
                "user_id": meta.get("user_id"),
                "problem_id": meta.get("problem_id"),
                "problem": problem.problem,
                "difficulty": problem.difficulty,
                "category": problem.category,
                "language": problem_lang.language,
                "function_name": problem_lang.function_name,
                "starter_code": problem_lang.starter_code,
                "test_cases": test_cases,
                "time_limit_seconds": time_limit_seconds,
                "start_at": start_at_str,
                "remaining_seconds": remaining_seconds,
            },
            status=status.HTTP_200_OK,
        )


class LiveCodingActiveSessionView(APIView):
    """
    현재 로그인한 사용자의 진행 중인 라이브 코딩 세션을 Redis에서 조회하는 엔드포인트.
    - Authorization: Bearer <access_token>
    - 응답: 세션이 있으면 LiveCodingSessionView와 동일한 구조, 없으면 404
    """

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "세션 정보를 조회하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        # 유저별 현재 세션 ID 조회
        mapping_key = f"livecoding:user:{user.user_id}:current_session"
        session_id = cache.get(mapping_key)
        if not session_id:
            return Response(
                {"detail": "진행 중인 라이브 코딩 세션이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        meta_key = f"livecoding:{session_id}:meta"

        meta = cache.get(meta_key)
        if not meta:
            return Response(
                {"detail": "세션 메타 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 다른 사용자의 세션에 접근하지 못하도록 검증
        if meta.get("user_id") != str(user.user_id):
            return Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        problem_id = meta.get("problem_id")
        language = meta.get("language")

        qs = (
            CodingProblemLanguage.objects.select_related("problem")
            .prefetch_related("problem__test_cases")
            .filter(problem__problem_id=problem_id)
        )
        if language:
            qs = qs.filter(language__iexact=language)

        problem_lang = qs.first()
        if not problem_lang:
            return Response(
                {"detail": "세션의 문제 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        problem = problem_lang.problem
        test_cases = [
            {"id": tc.id, "input": tc.input_data, "output": tc.output_data}
            for tc in (problem.test_cases.all() if hasattr(problem, "test_cases") else [])
        ]

        start_at_str = meta.get("start_at")
        time_limit_seconds = int(meta.get("time_limit_seconds") or 40 * 60)
        remaining_seconds = time_limit_seconds

        if start_at_str:
            try:
                start_at_dt = datetime.fromisoformat(start_at_str)
                if timezone.is_naive(start_at_dt):
                    start_at_dt = timezone.make_aware(start_at_dt, timezone=timezone.utc)
                elapsed = max(0, int((timezone.now() - start_at_dt).total_seconds()))
                remaining_seconds = max(0, time_limit_seconds - elapsed)
            except Exception:
                remaining_seconds = time_limit_seconds

        return Response(
            {
                "session_id": session_id,
                "state": meta.get("state"),
                "user_id": meta.get("user_id"),
                "problem_id": meta.get("problem_id"),
                "problem": problem.problem,
                "difficulty": problem.difficulty,
                "category": problem.category,
                "language": problem_lang.language,
                "function_name": problem_lang.function_name,
                "starter_code": problem_lang.starter_code,
                "test_cases": test_cases,
                "time_limit_seconds": time_limit_seconds,
                "start_at": start_at_str,
                "remaining_seconds": remaining_seconds,
            },
            status=status.HTTP_200_OK,
        )


class LiveCodingEndSessionView(APIView):
    """
    현재 로그인한 사용자의 진행 중인 라이브 코딩 세션을 종료(삭제)하는 엔드포인트.
    - Authorization: Bearer <access_token>
    - Redis에서 메타/매핑/STT 버퍼를 제거합니다.
    """

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "세션을 종료하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        mapping_key = f"livecoding:user:{user.user_id}:current_session"
        session_id = cache.get(mapping_key)
        if not session_id:
            # 이미 종료된 상태로 간주
            return Response(
                {"detail": "진행 중인 라이브 코딩 세션이 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        meta_key = f"livecoding:{session_id}:meta"
        code_key = f"livecoding:{session_id}:code"

        # 메타/코드/매핑 제거
        cache.delete(meta_key)
        cache.delete(code_key)
        cache.delete(mapping_key)

        # STT 버퍼도 함께 정리
        try:
            clear_utterances(str(session_id))
        except Exception:
            # 정리 실패는 치명적이지 않으므로 무시
            pass

        return Response(status=status.HTTP_204_NO_CONTENT)

def _format_birthdate(value):
    """birthdate가 문자열이든 date 객체든 안전하게 변환"""
    if not value:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, date):
        return value.isoformat()
    return None


class ProfileView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        return Response(
            {
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "birthdate": _format_birthdate(user.birthdate),
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        user = request.user
        data = request.data

        name = data.get("name")
        phone_number = data.get("phone_number")
        birthdate = data.get("birthdate")
        current_password = data.get("current_password")
        new_password = data.get("new_password")

        # 1. 필수 검증
        if not name:
            return Response({"detail": "이름은 필수 항목입니다."}, status=400)

        # 2. 전화번호 중복 체크
        if phone_number:
            existing = User.objects.filter(phone_number=phone_number).exclude(user_id=user.user_id).first()
            if existing:
                return Response({"detail": "이미 사용 중인 전화번호입니다."}, status=400)

        # 3. 비밀번호 변경
        if current_password and new_password:
            if not user.password_hash:
                return Response({"detail": "소셜 로그인 계정은 비밀번호를 변경할 수 없습니다."}, status=400)

            if not check_password(current_password, user.password_hash):
                return Response({"detail": "현재 비밀번호가 올바르지 않습니다."}, status=400)

            if len(new_password) < 8:
                return Response({"detail": "새 비밀번호는 8자 이상이어야 합니다."}, status=400)

            user.password_hash = make_password(new_password)

        elif current_password or new_password:
            return Response({"detail": "현재 비밀번호와 새 비밀번호를 모두 입력해주세요."}, status=400)

        # 4. birthdate 변환
        if birthdate:
            # 이미 날짜 형식 문자열일 경우 그대로 저장
            try:
                # 먼저 date 객체로 바꾸기 시도
                parsed = datetime.strptime(birthdate, "%Y-%m-%d").date()
                user.birthdate = parsed
            except Exception:
                # 문자열 그대로 저장해야 하는 경우도 있을 수 있음
                user.birthdate = birthdate
        else:
            user.birthdate = None

        # 5. 나머지 필드 저장
        user.name = name
        user.phone_number = phone_number if phone_number else None
        user.updated_at = timezone.now()

        user.save()

        return Response(
            {
                "message": "회원정보가 성공적으로 수정되었습니다.",
                "user_id": user.user_id,
                "email": user.email,
                "name": user.name,
                "phone_number": user.phone_number,
                "birthdate": _format_birthdate(user.birthdate),
            },
            status=status.HTTP_200_OK,
        )

# backend/api/views.py

class CodingQuestionView(APIView):
    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "질문 생성을 위해서는 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        session_id = request.data.get("session_id") or request.query_params.get("session_id")
        if not session_id:
            return Response(
                {"detail": "session_id가 필요합니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1) 세션 메타 / 코드 스냅샷 로드
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key) or {}
        if not meta:
            return Response(
                {"detail": "해당 세션 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if str(meta.get("user_id")) != str(getattr(user, "user_id", None)):
            return Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        question_cnt = int(meta.get("question_cnt") or 0)
        # 최대 3회까지만 질문
        if question_cnt >= 3:
            return Response(
                {
                    "skipped": True,
                    "reason": "max_questions_reached",
                    "question": "",
                    "tts_audio": [],
                },
                status=status.HTTP_200_OK,
            )

        code_key = f"livecoding:{session_id}:code"
        code_data = cache.get(code_key) or {}
        history = code_data.get("history") or []
        latest = code_data.get("latest") or {}

        if not latest:
            return Response(
                {
                    "skipped": True,
                    "reason": "no_code_snapshot",
                    "question": "",
                    "tts_audio": [],
                },
                status=status.HTTP_200_OK,
            )

        latest_code = latest.get("code") or ""
        language = (latest.get("language") or meta.get("language") or "python").lower()
        last_snapshot_index = int(meta.get("last_question_snapshot_index") or 0)
        snapshot_index = len(history) or 1

        last_question_text = (meta.get("last_question_text") or "").strip()

        # 이전에 질문을 했던 스냅샷 기준 코드 (없으면 빈 문자열)
        prev_code = ""
        if last_snapshot_index and 0 < last_snapshot_index <= len(history):
            try:
                prev_code = history[last_snapshot_index - 1].get("code") or ""
            except Exception:
                prev_code = ""

        starter_code = (meta.get("starter_code") or "").strip()

        # 2) LangGraph(chapter2) 호출
        graph = get_cached_graph(session_id=session_id, name="chapter2")
        coding_state = {
            "meta": {"session_id": session_id, "user_id": user.user_id},
            "code": latest_code,
            "language": language,
            "question_cnt": question_cnt,
             # 코드 진행도 판단용 보조 필드
            "starter_code": starter_code,
            "prev_code": prev_code,
            "snapshot_index": snapshot_index,
            "last_snapshot_index": last_snapshot_index,
            "last_question_text": last_question_text,
        }
        try:
            result = graph.invoke(
                coding_state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        "checkpoint_namespace": "chapter2",
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": "코딩 질문 그래프 호출에 실패했습니다.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        question_text = (
            (result.get("question") or "") or (result.get("tts_text") or "")
        ).strip()
        if not question_text:
            return Response(
                {
                    "skipped": True,
                    "reason": "empty_question",
                    "question": "",
                    "tts_audio": [],
                },
                status=status.HTTP_200_OK,
            )

        # 3) 질문 횟수/스냅샷 인덱스 메타에 반영
        meta["question_cnt"] = question_cnt + 1
        meta["last_question_snapshot_index"] = snapshot_index
        meta["last_question_text"] = question_text
        cache.set(meta_key, meta, timeout=60 * 60)

        # 4) 질문 텍스트를 TTS로 변환해 프론트로 내려줌
        try:
            tts_chunks = _generate_tts_payload(
                question_text,
                session_id=session_id,
                max_sentences=2,
            )
        except Exception:
            tts_chunks = []

        return Response(
            {
                "skipped": False,
                "reason": None,
                "question": question_text,
                "tts_audio": tts_chunks,
                "state": result,
            },
            status=status.HTTP_200_OK,
        )
