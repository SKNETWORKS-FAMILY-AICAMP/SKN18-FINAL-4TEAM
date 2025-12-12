import json
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .interview_utils import get_cached_graph, get_cached_llm, intro_tts_payload
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
                        "thread_id": session_id,
                        # 세션별로 체크포인트 네임스페이스를 분리해 이전 세션 문제 데이터가 섞이지 않도록 한다.
                        "checkpoint_namespace": f"chapter1",
                    }
                },
            )
            if isinstance(graph_state, dict):
                intro_text = graph_state.get("tts_text") or ""
                sentences_payload = intro_tts_payload(intro_text, session_id)
        
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
        session_id = None
        if isinstance(data, dict):
            session_id = data.get("session_id")

        stt_text = (data.get("stt_text") or "").strip()
        event_type = "strategy_submit"

        if not stt_text:
            return Response(
                {"detail": "stt_text 필드를 비울 수 없습니다."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        graph = get_cached_graph(name="chapter1")

        update_state = {
            "meta": {
                "session_id": session_id,
            },
            
            "event_type": event_type,
            "stt_text": stt_text,
        }

        try:
            result_state = graph.invoke(
                update_state,
                config={
                    "configurable": {
                        "thread_id": session_id,
                        # 세션별로 체크포인트 네임스페이스를 분리해 이전 세션 문제 데이터가 섞이지 않도록 한다.
                        "checkpoint_namespace": f"chapter1",
                    }
                },
            )
           
                
        except Exception as exc:  # noqa: BLE001
            return Response(
                {"error": "langgraph invoke failed", "detail": str(exc)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
            
        tts_text = ""
        user_answer_class = None
        sentences_payload = []
        non_strategy_count = 0
        if isinstance(result_state, dict):
            tts_text = result_state.get("tts_text") or ""
            user_answer_class = (result_state.get("user_answer_class") or "").strip() or None
            sentences_payload = intro_tts_payload(tts_text, session_id)
            non_strategy_count = int(result_state.get("intro_non_strategy_count") or 0)

        # 다음 단계/세션 종료 여부 결정: LangGraph state만으로 판정
        stage = "intro"
        if user_answer_class == "strategy":
            stage = "coding"
        elif user_answer_class != "strategy" and non_strategy_count >= 2:
            stage = "end_session"

        response_payload = {
            "tts_text": sentences_payload,
            "user_answer_class": user_answer_class,
            "stage": stage,
        }

        return Response(response_payload, status=status.HTTP_200_OK)
