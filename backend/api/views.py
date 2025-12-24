from datetime import datetime, timedelta, date
import json
import secrets
import string
import time
import threading
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
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated

from .email_utils import send_verification_code, verify_code
from .throttling import (
    EmailActionRateThrottle,
    LoginRateThrottle,
    PasswordResetRateThrottle,
)
from .stt_buffer import clear_utterances
from .google_oauth import GoogleOAuthError, exchange_code_for_tokens, fetch_userinfo
from .jwt_utils import create_access_token
from .interview_utils import _generate_tts_payload, get_cached_graph

from .models import (
    AuthIdentity,
    CodingProblem,
    CodingProblemLanguage,
    TestCase,
    User,
    LivecodingReport,
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

class TTSView(APIView):
    """
    텍스트를 받아 TTS만 수행하는 엔드포인트.
    - POST /api/tts/intro/?session_id=...
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
    라이브 코딩 세션을 시작하면서 세션 정보를 저장하는 엔드포인트.
    - Authorization: Bearer <access_token> (LoginView/GoogleAuthView에서 발급한 토큰)
    - 저장되는 키: livecoding:{session_id}:meta, 
      값: { state, problem_id, user_id, session_id }
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "라이브 코딩을 시작하려면 로그인이 필요합니다."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        problem_data = request.data.get("problem_data")
        if not isinstance(problem_data, dict):
            return Response({"detail": "problem_data가 필요합니다."}, status=400)
        required = ["problem_id", "problem", "difficulty", "category", "language", "function_name", "starter_code", "test_cases"]
        missing = [k for k in required if k not in problem_data]
        if missing:
            return Response({"detail": f"problem_data 필드 누락: {', '.join(missing)}"}, status=400)
        session_id = secrets.token_hex(16)
        start_at = timezone.now() # Redis(캐시)에 저장할 세션 메타 정보
        meta = {
            "stage": "intro",
            "user_id": user.user_id,
            "session_id": session_id,
            "time_limit_seconds": int(problem_data.get("time_limit_seconds") or 40 * 60),
            "start_at": start_at.isoformat(),
        }
        problem_payload  = {
                "problem_id": problem_data["problem_id"],
                "problem": problem_data['problem'],
                "difficulty": problem_data['difficulty'],
                "category": problem_data['category'],
                "language": problem_data['language'],
                "function_name":  problem_data['function_name'],
                "starter_code": problem_data['starter_code'],
                "test_cases":  problem_data['test_cases'],
            
        }

        cache.set(f"livecoding:{session_id}:meta", meta, timeout=60*60)
        cache.set(f"livecoding:{session_id}:problem", problem_payload, timeout=60*60)
        cache.set(f"livecoding:user:{user.user_id}:current_session", session_id, timeout=60*60)
        return Response(
            {
                "session_id": session_id,
                "state": meta["stage"],
                "time_limit_seconds": meta["time_limit_seconds"],
                "start_at": meta["start_at"],
                "remaining_seconds": meta["time_limit_seconds"],
                "problem_data": problem_payload,
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
        real_algorithm_category = data.get("problem_algorithm_category") or ""
        problem_description = data.get("problem_description") or ""
        hint_trigger = data.get("hint_trigger") or "manual"
        conversation_log = data.get("conversation_log") if isinstance(data.get("conversation_log"), list) else None
        hint_count_raw = data.get("hint_count")
        test_cases_payload = data.get("test_cases")
        hint_request_text = (data.get("hint_request_text") or "").strip()

        # 메타에 저장된 힌트 사용 횟수(재접속 시 복원용)
        meta_hint_count_raw = meta.get("hint_count")
        try:
            meta_hint_count = int(meta_hint_count_raw) if meta_hint_count_raw is not None else 0
        except Exception:
            meta_hint_count = 0

        try:
            hint_count = int(hint_count_raw) if hint_count_raw is not None else None
        except Exception:
            hint_count = None

        # 최종 기준 힌트 횟수:
        # - meta에 저장된 값이 있으면 우선 사용
        # - 없고, 요청에만 값이 있으면 그 값을 사용
        # - 모두 없으면 대화 로그에서 추정, 그것도 없으면 0
        if hint_count is None:
            if meta_hint_count:
                hint_count = meta_hint_count
            elif conversation_log:
                hint_count = sum(
                    1
                    for entry in conversation_log
                    if isinstance(entry, dict) and entry.get("type") == "hint"
                )
            else:
                hint_count = 0
        else:
            # 클라이언트와 메타값이 모두 있을 경우 더 큰 값을 사용해 불일치 최소화
            hint_count = max(hint_count, meta_hint_count)

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


        # 사용자의 초기 전략 답변(문제 접근 방식)이 저장되어 있다면 함께 전달
        strategy_answer = (meta.get("strategy_answer") or "").strip()

        state = {
            "meta": {"session_id": session_id, "user_id": str(user.user_id)},
            "current_user_code": code,
            "problem_description": problem_description,
            "real_algorithm_category": real_algorithm_category,
            "hint_trigger": hint_trigger,
            "hint_count": hint_count,
            "user_strategy_answer": strategy_answer,
            "hint_request_text": hint_request_text,
        }
        if conversation_log is not None:
            state["conversation_log"] = conversation_log

        try:
            graph = get_cached_graph(name="chapter2_hint")
            result_state = graph.invoke(
                state,
                config={
                    "configurable": {
                        "thread_id":f"{session_id}:chapter2_hint"
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": "langgraph invoke failed", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        hint_text = (result_state.get("hint_text") or "").strip()
        new_hint_count = result_state.get("hint_count", hint_count)

        # 최신 힌트 사용 횟수를 세션 메타에 저장해서 재접속 시 복원 가능하게 함
        try:
            meta["hint_count"] = int(new_hint_count)
        except Exception:
            meta["hint_count"] = new_hint_count
        cache.set(meta_key, meta, timeout=60 * 60)

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
                "hint_count": new_hint_count,
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
    # ✅ 추가: 명시적으로 인증 클래스 지정
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

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
        problem_key = f"livecoding:{session_id}:problem"

        meta = cache.get(meta_key)
        if not meta:
            return Response(
                {"detail": "해당 세션 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # 다른 사용자의 세션에 접근하지 못하도록 검증
        if str(meta.get("user_id")) != str(user.user_id):
            return Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )

        problem = cache.get(problem_key) or {}
        if not problem:
            return Response(
                {"detail": "세션의 문제 정보를 찾을 수 없습니다."},
                status=status.HTTP_404_NOT_FOUND,
            )

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
                "stage": meta.get("stage"),
                "user_id": meta.get("user_id"),
                "problem_id": problem.get("problem_id") or meta.get("problem_id"),
                "problem": problem.get("problem"),
                "difficulty": problem.get("difficulty"),
                "category": problem.get("category"),
                "language": problem.get("language") or meta.get("language"),
                "function_name": problem.get("function_name"),
                "starter_code": problem.get("starter_code"),
                "test_cases": problem.get("test_cases") or [],
                "time_limit_seconds": time_limit_seconds,
                "start_at": start_at_str,
                "remaining_seconds": remaining_seconds,
                "hint_count": int(meta.get("hint_count") or 0),
            },
            status=status.HTTP_200_OK,
        )


class LiveCodingActiveSessionView(APIView):
    """
    현재 로그인한 사용자의 진행 중인 라이브 코딩 세션을 Redis에서 조회하는 엔드포인트.
    - Authorization: Bearer <access_token>
    - 응답: 세션이 있으면 LiveCodingSessionView와 동일한 구조, 없으면 404
    """
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

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
                {"available": False},
                status=status.HTTP_200_OK,
            )

        meta_key = f"livecoding:{session_id}:meta"
        problem_key =  f"livecoding:{session_id}:problem"
        meta = cache.get(meta_key)
        problem = cache.get(problem_key)
        if not meta and problem:
            return Response(
                {"available": False},
                status=status.HTTP_200_OK,
            )

        # 다른 사용자의 세션에 접근하지 못하도록 검증
        if meta.get("user_id") != str(user.user_id):
            return Response(
                {"detail": "이 세션에 접근할 권한이 없습니다."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        problem_id = problem.get("problem_id")
        language = problem.get("language")

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
    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

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

        # 1) 세션 메타 / 문제 정보 / 코드 스냅샷 로드
        meta_key = f"livecoding:{session_id}:meta"
        problem_key = f"livecoding:{session_id}:problem"
        code_key = f"livecoding:{session_id}:code"
        code_data = cache.get(code_key) or {}

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

        # 문제 정보는 별도 키(livecoding:{session_id}:problem)에 저장된다.
        # starter_code, 실제 문제 언어 등은 여기에서 가져오고,
        # meta에는 세션 진행 상태(state, stage, question_cnt 등만 둔다.
        problem = cache.get(problem_key) or {}

        question_cnt = int(code_data.get("question_cnt") or 0)
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
        # 언어는 코드 스냅샷에 없으면 문제/메타 순으로 fallback
        language = (
            problem.get("language")
        ).lower()

        last_question_text = (code_data.get("last_question_text") or "").strip()

        # 질문용 코드 스냅샷 히스토리:
        # 사용자가 타이핑할 때마다 저장되는 history 전체가 아니라,
        # "질문이 실제로 생성되었던 시점"의 코드만 따로 모아 둔다.
        question_history = code_data.get("question_history") or []

        # 이전 질문이 있었다면 그 시점의 코드 스냅샷을 prev_code로 사용
        prev_code = ""
        if question_history:
            try:
                prev_code = question_history[-1].get("code") or ""
            except Exception:
                prev_code = ""

        # starter_code는 문제 payload에만 존재하므로, 먼저 problem에서 찾고
        # 과거 메타에 저장된 값이 있다면 보조적으로만 사용한다.
        starter_code = (
            (problem.get("starter_code") or "")
        ).strip()

        # 2) LangGraph(chapter2) 호출
        graph = get_cached_graph(name="chapter2")
        coding_state = {
            "meta": {"session_id": session_id, "user_id": user.user_id},
            "code": latest_code,
            "language": language,
            "question_cnt": question_cnt,
             # 코드 진행도 판단용 보조 필드
            "starter_code": starter_code,
            "prev_code": prev_code,
            "last_question_text": last_question_text,
        }
        try:
            result = graph.invoke(
                coding_state,
                config={
                    "configurable": {
                        "thread_id":f"{session_id}:chapter2"
                    }
                },
            )
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"detail": "코딩 질문 그래프 호출에 실패했습니다.", "error": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        question_text = (result.get("tts_text") or "").strip()
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

        # 3) 질문 횟수/질문 기준 코드 스냅샷 메타에 반영
        code_data["question_cnt"] = question_cnt + 1
        code_data["last_question_text"] = question_text
        cache.set(meta_key, meta, timeout=60 * 60)

        # 이번 질문 생성에 실제로 사용한 코드 스냅샷을 별도로 보관해
        # 다음 질문에서 prev_code로 사용한다.
        question_history.append(latest)
        # 메모리 보호를 위해 최근 50개까지만 유지
        if len(question_history) > 50:
            question_history = question_history[-50:]
        code_data["question_history"] = question_history
        cache.set(code_key, code_data, timeout=60 * 60)

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

class LiveCodingFinalEvalStartView(APIView):
    """
    제출하기 버튼 트리거:
    - POST /api/livecoding/final-eval/start/
      body: {"session_id": "..."}
    - 즉시 202 반환하고, 백그라운드 스레드에서 chapter3 graph 실행 시작
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        session_id = (request.data or {}).get("session_id")
        if not session_id:
            return Response({"detail": "session_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 소유권 검증 (중요)
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key)
        if not meta:
            return Response({"detail": "해당 세션 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if str(meta.get("user_id")) != str(user.user_id):
            return Response({"detail": "이 세션에 접근할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        # ✅ 백그라운드 실행
        def _runner():
            try:
                graph = get_cached_graph("chapter3")
                config = {"configurable": {"thread_id": f"{session_id}:chapter3"}}

                # 최소 상태로 시작(노드 없으면 그래도 저장되도록)
                init_state = {
                    "meta": {"session_id": session_id, "user_id": str(user.user_id)},
                    "step": "init",
                    "status": "running",
                }

                graph.invoke(init_state, config=config)

                # 그래프가 정상 종료되면 마지막 상태를 'saved/done'으로 맞춰두는 걸 추천
                # (노드에서 처리해도 되고, 여기서 한 번 더 저장해도 됨)
                try:
                    # 최신 상태를 읽어서 step/status만 보정
                    snap = graph.get_state(config)
                    values = dict(snap.values or {})
                    values["step"] = values.get("step") or "saved"
                    values["status"] = "done"
                    # invoke가 체크포인터에 저장했겠지만, 보정 저장이 필요하면 노드에서 하거나
                    # 그래프 마지막 노드에서 saved로 세팅해.
                except Exception:
                    pass

            except Exception as e:
                # 에러 상태를 체크포인터에 남기고 싶으면
                try:
                    graph = get_cached_graph("chapter3")
                    config = {"configurable": {"thread_id": f"{session_id}:chapter3"}}
                    err_state = {
                        "meta": {"session_id": session_id, "user_id": str(user.user_id)},
                        "step": "error",
                        "status": "error",
                        "error": str(e),
                    }
                    # graph.invoke 대신 저장만 하고 싶으면 체크포인터 접근이 필요하지만
                    # 여기서는 최소로 "에러 상태를 state로 남길 수 있게" graph에 error node를 두는 걸 추천.
                    # (지금은 그냥 출력)
                except Exception:
                    pass

        threading.Thread(target=_runner, daemon=True).start()

        return Response({"status": "started"}, status=status.HTTP_202_ACCEPTED)


class LiveCodingFinalEvalStatusView(APIView):
    """
    rendering.vue 폴링용:
    - GET /api/livecoding/final-eval/status/?session_id=...
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response({"detail": "session_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 소유권 검증(권장)
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key)
        if meta and str(meta.get("user_id")) != str(user.user_id):
            return Response({"detail": "이 세션에 접근할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        graph = get_cached_graph("chapter3")
        config = {"configurable": {"thread_id": f"{session_id}:chapter3"}}

        try:
            snap = graph.get_state(config)
            values = snap.values or {}
        except Exception:
            values = {}

        # 그래프가 아직 시작 안됐거나 저장된 게 없으면 init으로 응답
        step = values.get("step") or "init"
        st = values.get("status") or ("done" if step == "saved" else "running")

        return Response(
            {
                "status": st,
                "step": step,
                **values,
            },
            status=status.HTTP_200_OK,
        )
class LiveCodingFinalEvalReportView(APIView):
    """
    showreport.vue 용:
    - GET /api/livecoding/final-eval/report/?session_id=...
    - done이면 report/score/grade 반환
    - 아직 running이면 202로 반환
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        session_id = request.query_params.get("session_id")
        if not session_id:
            return Response({"detail": "session_id가 필요합니다."}, status=status.HTTP_400_BAD_REQUEST)

        # 세션 소유권 검증
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key)
        if not meta:
            return Response({"detail": "해당 세션 정보를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        if str(meta.get("user_id")) != str(user.user_id):
            return Response({"detail": "이 세션에 접근할 권한이 없습니다."}, status=status.HTTP_403_FORBIDDEN)

        graph = get_cached_graph("chapter3")
        config = {"configurable": {"thread_id": f"{session_id}:chapter3"}}

        try:
            snap = graph.get_state(config)
            values = dict(snap.values or {})
        except Exception as e:
            return Response(
                {"detail": "final-eval state를 읽을 수 없습니다.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        step = values.get("step") or "init"
        st = values.get("status") or ("done" if step == "saved" else "running")

        if st != "done" or step != "saved":
            return Response(
                {"status": st, "step": step},
                status=status.HTTP_202_ACCEPTED,
            )

        report_md = values.get("final_report_markdown") or ""
        
        graph_output = values.get("graph_output") or {}

        # graph_output에 problem_text가 없으면 여러 소스에서 최대한 찾아 채움
        if not graph_output.get("problem_text"):
            try:
                problem_text = None

                # 0) (혹시 로컬 meta에 이미 들어있으면)
                if isinstance(meta, dict):
                    problem_text = (
                        meta.get("problem_text")
                        or meta.get("problem_description")
                        or meta.get("problem")
                    )

                # 1) 세션 meta 캐시에서 (livecoding:{session_id}:meta)
                if not problem_text:
                    meta_key = f"livecoding:{session_id}:meta"
                    cached_meta = cache.get(meta_key) or {}
                    if isinstance(cached_meta, dict):
                        problem_text = (
                            cached_meta.get("problem_text")
                            or cached_meta.get("problem_description")
                            or cached_meta.get("problem")
                        )
                        # problem_payload / problem_data 형태로 들어있을 수도 있음
                        if not problem_text:
                            pd = cached_meta.get("problem_payload") or cached_meta.get("problem_data") or {}
                            if isinstance(pd, dict):
                                problem_text = pd.get("problem") or pd.get("problem_text") or pd.get("problem_description")

                # 2) 별도 problem 캐시 키가 있다면 (프로젝트마다 다르게 저장하는 경우 대비)
                if not problem_text:
                    for k in (f"livecoding:{session_id}:problem", f"livecoding:{session_id}:problem_data"):
                        pd = cache.get(k) or {}
                        if isinstance(pd, dict):
                            problem_text = pd.get("problem") or pd.get("problem_text") or pd.get("problem_description")
                            if problem_text:
                                break

                # 3) code 캐시에서
                if not problem_text:
                    code_key = f"livecoding:{session_id}:code"
                    code_data = cache.get(code_key) or {}
                    if isinstance(code_data, dict):
                        problem_text = (
                            code_data.get("problem_text")
                            or code_data.get("problem_description")
                            or code_data.get("problem")
                        )

                if problem_text:
                    graph_output["problem_text"] = problem_text
                    values["graph_output"] = graph_output  # ✅ 중요: values에 다시 박아줘야 return에서도 유지됨
                    print(f"[✓ 리포트 API] 문제 텍스트 추가: {len(problem_text)}자", flush=True)
                else:
                    values["graph_output"] = graph_output
                    print("[✗ 리포트 API] problem_text를 어디에서도 찾지 못했습니다.", flush=True)

            except Exception as e:
                values["graph_output"] = graph_output
                print(f"[✗ 리포트 API] 문제 텍스트 로드 실패: {e}", flush=True)
        try:
            from api.models import LivecodingReport  # 지연 import로 순환참조 회피

            defaults = {
                "user": user,
                "report_md": report_md,
                "final_score": values.get("final_score"),
                "final_grade": values.get("final_grade"),
                "final_flags": values.get("final_flags") or [],
                "graph_output": values.get("graph_output") or {},
                "problem_eval_score": values.get("problem_eval_score"),
                "problem_eval_feedback": values.get("problem_eval_feedback"),
                "code_collab_score": values.get("code_collab_score"),
                "code_collab_feedback": values.get("code_collab_feedback"),
                "problem_evidence": values.get("problem_evidence"),
                "code_collab_evidence": values.get("code_collab_evidence"),
                "step": values.get("step"),
                "status": values.get("status"),
                "error": values.get("error"),
            }
            LivecodingReport.objects.update_or_create(
                session_id=session_id,
                defaults=defaults,
            )
        except Exception as e:
            # 저장 실패는 조회 응답을 막지 않음
            print(f"[report_api] livecoding_reports upsert failed: {e}", flush=True)
        return Response(
            {
                "status": "done",
                "step": "saved",
                "final_report_markdown": report_md,
                "final_score": values.get("final_score"),
                "final_grade": values.get("final_grade"),
                "final_flags": values.get("final_flags", []),
                "graph_output": values.get("graph_output"),  # 위에서 values에 다시 저장했기 때문에 안전
            },
            status=status.HTTP_200_OK,
        )



class LiveCodingReportListView(APIView):
    """
    DB에 저장된 최종 리포트 목록 (로그인 사용자 본인)
    GET /api/livecoding/reports/
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        reports = (
            LivecodingReport.objects.filter(user=user)
            .order_by("-created_at", "-id")
        )
        results = []
        for r in reports:
            results.append(
                {
                    "session_id": r.session_id,
                    "final_score": r.final_score,
                    "final_grade": r.final_grade,
                    "final_flags": r.final_flags or [],
                    "has_report": bool(r.report_md),
                    "has_pdf": bool(r.pdf_path),
                    "pdf_path": r.pdf_path,
                    "created_at": r.created_at.isoformat() if r.created_at else None,
                    "updated_at": r.updated_at.isoformat() if r.updated_at else None,
                }
            )

        return Response({"results": results}, status=status.HTTP_200_OK)


class LiveCodingReportDetailView(APIView):
    """
    DB에 저장된 최종 리포트 상세 (로그인 사용자 본인)
    GET /api/livecoding/reports/<session_id>/
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, session_id: str):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response({"detail": "로그인이 필요합니다."}, status=status.HTTP_401_UNAUTHORIZED)

        report = LivecodingReport.objects.filter(session_id=session_id, user=user).first()
        if not report:
            return Response({"detail": "리포트를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        return Response(
            {
                "status": report.status or "done",
                "step": report.step or "saved",
                "session_id": report.session_id,
                "final_report_markdown": report.report_md or "",
                "final_score": report.final_score,
                "final_grade": report.final_grade,
                "final_flags": report.final_flags or [],
                "graph_output": report.graph_output or {},
                "problem_eval_score": report.problem_eval_score,
                "problem_eval_feedback": report.problem_eval_feedback,
                "code_collab_score": report.code_collab_score,
                "code_collab_feedback": report.code_collab_feedback,
                "problem_evidence": report.problem_evidence,
                "code_collab_evidence": report.code_collab_evidence,
                "error": report.error,
                "pdf_path": report.pdf_path,
                "created_at": report.created_at.isoformat() if report.created_at else None,
                "updated_at": report.updated_at.isoformat() if report.updated_at else None,
            },
            status=status.HTTP_200_OK,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def save_strategy_answer(request):
    """chapter1 전략 답변을 명시적으로 저장"""
    session_id = request.data.get("session_id")
    strategy_answer = request.data.get("strategy_answer")
    
    if not session_id or not strategy_answer:
        return Response(
            {"error": "session_id and strategy_answer required"}, 
            status=400
        )
    
    try:
        # Redis cache에 저장
        meta_key = f"livecoding:{session_id}:meta"
        meta = cache.get(meta_key) or {}
        meta["strategy_answer"] = strategy_answer
        cache.set(meta_key, meta, 3600)
        
        print(f"[save_strategy] 저장 완료: {strategy_answer[:50]}...", flush=True)
        
        return Response({
            "success": True,
            "message": "Strategy answer saved",
            "length": len(strategy_answer),
        })
        
    except Exception as e:
        print(f"[save_strategy] 오류: {e}", flush=True)
        import traceback
        traceback.print_exc()
        return Response(
            {"error": str(e)}, 
            status=500
        )
