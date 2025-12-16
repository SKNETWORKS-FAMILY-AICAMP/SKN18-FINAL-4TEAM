import json
from django.core.cache import cache
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .interview_utils import get_cached_graph, get_cached_llm, _generate_tts_payload
from .models import (
    CodingProblemLanguage,
    User,
)


class WarmupLanggraphView(APIView):
    """
    Langgraph/LLM 모듈을 미리 로드하기 위한 워밍업 엔드포인트.
    """

    def get(self, request):
        try:
            # LLM 모듈 import 및 그래프 컴파일 시도
            llm_instance = get_cached_llm()
            _ = llm_instance   # LLM은 존재 확인
        
            graph1 = get_cached_graph(name="chapter1")
            graph1.get_graph()  # 실제 실행은 하지 않고 DAG만 준비
            return Response(
                {
                    "status": "warmed",
                }, 
                status=status.HTTP_200_OK)
        
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"status": "error", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

class LiveCodingPreloadView(APIView):
    """
    문제를 미리 선택해 내려주는 엔드포인트. (TTS 텍스트 생성은 CodingProblemTextInitView에서 수행)

    - Authorization: Bearer <access_token>
    - 요청 본문:
        - language (optional): 기본값 python, 해당 언어로 랜덤 선택
    - 응답:
        - 문제 정보(problem_id, 문제 본문, 테스트케이스 등)
    """

    def post(self, request):
        user = getattr(request, "user", None)
        if not isinstance(user, User):
            return Response(
                {"detail": "라이브 코딩을 준비하려면 로그인이 필요합니다."},
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
            detail = f"요청한 언어({language})의 문제를 찾을 수 없습니다."
            return Response({"detail": detail}, status=status.HTTP_404_NOT_FOUND)

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
            },
            status=status.HTTP_200_OK,
        )
        
class CodingProblemTextInitView(APIView):
    """
    인트로용 tts_text(텍스트만)를 반환하는 경량 엔드포인트.

    - POST /api/coding-problems/session/init/:
      body: RandomCodingProblemView 응답 전체(JSON) + session_id
      response: {"tts_text": "...", "session_id": "...", "stage": "intro"}
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
            
        user_id = request.user.user_id if hasattr(request, "user") else None

        session_id = None
        if isinstance(request.data, dict):
            session_id = request.data.get("session_id")
 
        init_state = {
            "meta": {
                "user_id": user_id,
                "session_id": session_id,
            },
            "event_type": "init",
            "problem_data": problem_text,
            "intro_flow_done": False,
        }
        intro_text = ""
        try:
            graph = get_cached_graph(name ="chapter1")
            graph_state = graph.invoke(
                init_state,
                config={
                    "configurable": {
                        "thread_id": f"{session_id}:chapter1"
                    }
                },
            )
            if isinstance(graph_state, dict):
                intro_text = graph_state.get("tts_text") or ""
                sentences_payload = _generate_tts_payload(intro_text, session_id)
        
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
                "tts_text": sentences_payload,
                "session_id": session_id,
                "stage": "intro",
            },
            status=status.HTTP_200_OK,
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
                coding_graph = get_cached_graph(name="chapter2")
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
                            "thread_id": f"{session_id}:chapter2"
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
                    "intro_flow_done": False,
                    "stage": "coding",
                    "coding_intro_text": "",
                },
                status=status.HTTP_200_OK,
            )

        graph = get_cached_graph(name="chapter1")

        update_state = {
            "event_type": event_type,
            "stt_text": stt_text,
        }

        try:
            result_state = graph.invoke(
                update_state,
                config={
                    "configurable": {
                        "thread_id":f"{session_id}:chapter1"
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
                            "thread_id": f"{session_id}:chapter2"
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
