from interview_engine.state import InterviewState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 
from datetime import datetime
from typing import Any, Dict
import json


def now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _get_problem_text(state: InterviewState) -> str:
    """state.problem_data는 문자열만 기대한다."""
    return str(state.get("problem_data") or "")


def _get_answer_class(state: InterviewState) -> str:
    intro = state.get("intro") or {}
    return str(intro.get("user_answer_class") or "").lower()


def _mark_meta(meta: dict, stage: str = "intro"
                , intro_flow_done:bool = False ) -> None:
    meta.setdefault("created_at", now_iso())
    meta["updated_at"] = now_iso()
    meta["stage"] = stage
    # intro_flow_done은 후속 단계에서 True로 갱신될 수 있으므로 덮어쓴다
    meta["intro_flow_done"] = intro_flow_done


def problem_intro_agent(state: InterviewState) -> InterviewState:
    """
    Step 1: Problem Introduction + Q&A Agent

    사용하는 state 필드:
        - problem_data: 문제 설명 텍스트 (str)
        - user_question: (선택) 사용자가 말한 질문 텍스트 (str)
        - meta: MetaState
        - intro: IntroState

    동작:
        - Intro 모드 (user_question 없음):
            - smalltalk + 문제 요약 + 풀이 전략 질문까지 포함된 TTS 멘트 생성
            - intro.intro_text, intro.strategy_question 에 저장
            - tts_text 에 intro_text 저장
        - Q&A 모드 (user_question 있음):
            - 문제 관련 질문에 대한 답변 멘트 생성
            - intro.problem_answer, intro.followup_text 에 저장
            - tts_text 에 답변 저장
    """

    # 1) 문제/질문 텍스트 가져오기
    problem: str = _get_problem_text(state)
    intro = state.setdefault("intro", {})
    meta = state.setdefault("meta", {})

    # 분류 결과로 모드 판단
    answer_class = _get_answer_class(state)
    is_question = answer_class == "problem_question"
    user_question: str = intro.get("user_question") if is_question else ""

    problem_context = f"문제 설명:\n{problem}\n"

    # ─────────────────────────────────────────
    # 모드 판단
    # ─────────────────────────────────────────
    mode = "qna" if user_question.strip() else "intro"

    # ─────────────────────────────────────────
    # Intro 모드: intro_text + strategy_question 을 JSON으로 받아오기
    # ─────────────────────────────────────────
    if mode == "intro":
        system_prompt = (
            "당신은 AI 기반 코딩 테스트의 음성 면접관입니다.\n"
            "당신의 출력은 음성 합성(TTS)을 통해 지원자에게 전달됩니다.\n\n"
            "현재는 문제 소개 단계입니다. 당신은 두 가지를 생성해야 합니다.\n\n"
            "1. intro_text:\n"
            "   - 지원자의 긴장을 풀어주는 간단한 인사 한두 문장\n"
            "   - 이어서 문제의 핵심 요약\n"
            "   - TTS 친화적인 표현만 사용\n\n"
            "2. strategy_question:\n"
            "   - 사용자가 음성으로 풀이 전략을 설명하도록 유도하는 질문\n"
            "   - 예: 어떤 알고리즘을 사용할지, 자료구조 선택, 시간 복잡도 고려 등\n\n"
            "출력은 반드시 다음 JSON 형식을 지켜야 합니다.\n"
            "{\n"
            '  \"intro_text\": \"...\",\n'
            '  \"strategy_question\": \"...\"\n'
            "}\n\n"
            "규칙:\n"
            "1) 모든 문장은 '습니다', '니다'로 끝나야 합니다.\n"
            "2) TTS 친화적 표현만 사용하세요.\n"
            "   - Markdown 기호(백틱, 별표, 샵, 대시 등)와 특수문자 사용을 피하세요.\n"
            "   - 변수명은 괄호로 읽기 쉽게 풀어쓰기 (예: user_id는 '유저 아이디').\n"
            "   - 수식은 말로 풀어쓰기 (예: a <= 100 → '에이가 백 이하').\n"
            "3) intro_text는 약 2~4문장, strategy_question은 1문장으로 작성하세요.\n"
        )

        human_prompt = (
            "아래는 코딩 테스트 문제 정보입니다.\n\n"
            f"{problem_context}\n\n"
            "문제 소개 멘트(intro_text)와 풀이 전략 질문(strategy_question)을 "
            "위의 JSON 형식에 맞추어 생성해 주세요."
        )

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt),
        ]

        try:
            response = LLM.invoke(messages)
            raw = (getattr(response, "content", "") or "").strip()

            intro_text = ""
            strategy_question = ""

            # JSON 파싱 시도
            try:
                data: Dict[str, Any] = json.loads(raw)
                intro_text = str(data.get("intro_text", "") or "").strip()
                strategy_question = str(data.get("strategy_question", "") or "").strip()
                # 혹시 하나라도 비어 있으면 fallback
                if not intro_text or not strategy_question:
                    raise ValueError("empty field")
            except Exception:
                # LLM이 JSON 형식 안 지킨 경우: 전체를 intro_text로 쓰고, 전략 질문은 기본값
                intro_text = raw
                strategy_question = (
                    "이제 이 문제를 어떻게 풀 계획인지, 사용할 알고리즘과 자료구조, "
                    "예상 시간 복잡도를 포함해서 풀이 전략을 말로 설명해 주실 수 있을까요?"
                )

            # state 반영
            intro["intro_text"] = intro_text
            intro["strategy_question"] = strategy_question

            # 최초 TTS 출력은 소개 멘트와 전략 질문을 함께 전달
            state["tts_text"] = f"{intro_text}\n{strategy_question}"
            state["await_human"] = True

            # meta 업데이트
            _mark_meta(meta, stage="intro")

        except Exception:
            # 실패 시 state 그대로
            return state

        return state

    # ─────────────────────────────────────────
    # Q&A 모드: 문제 관련 질문에 대한 답변 생성
    # ─────────────────────────────────────────
    system_prompt_qna = (
        "당신은 AI 기반 코딩 테스트의 음성 면접관입니다.\n"
        "당신의 출력은 음성 합성(TTS)을 통해 지원자에게 전달됩니다.\n\n"
        "지원자가 방금 문제에 대해 질문을 했습니다.\n"
        "질문에 대해 친절하고 명확하게 답변해 주세요.\n"
        "만약 질문이 문제와 전혀 상관 없거나, 코딩 테스트와 관련이 없어 보인다면\n"
        "현재는 코딩 테스트 문제에 대해 이야기하는 시간이라는 점을 부드럽게 알려주고,\n"
        "문제나 풀이 전략과 관련된 질문을 다시 요청해 주세요.\n\n"
        f"[문제 정보]\n{problem_context}\n\n"
        "[출력 규칙]\n"
        "1) 모든 문장은 '습니다', '니다'로 끝나야 합니다.\n"
        "2) TTS 친화적 표현만 사용하세요. Markdown 기호나 복잡한 수식은 피하세요.\n"
        "3) 문장은 너무 길지 않게, 짧고 명확하게 작성해 주세요.\n"
    )

    human_prompt_qna = (
        f"[지원자 질문]\n{user_question}\n\n"
        "위 질문에 대해 코딩 테스트 면접관의 입장에서 답변을 작성해 주세요."
    )

    messages_qna = [
        SystemMessage(content=system_prompt_qna),
        HumanMessage(content=human_prompt_qna),
    ]

    try:
        response = LLM.invoke(messages_qna)
        content = (getattr(response, "content", "") or "").strip()
        if not content:
            content = "질문에 대한 답변을 준비하지 못했습니다."

        # Q&A 답변을 intro 영역에 저장
        intro["problem_answer"] = content
        # TTS로 읽을 텍스트
        state["tts_text"] = content + "\n" + "문제 이해는 되셨나요?  그렇다면 이 문제를 어떻게 접근하실지, 풀이 전략을 설명해주시겠어요?"
        # meta 갱신 (단계는 아직 intro / 전략 수집 단계일 수 있음)
        _mark_meta(meta, stage="intro", intro_flow_done = True)
        state["await_human"] = True

    except Exception:
        # LLM 실패 시에도 플로우가 끊기지 않도록 기본 멘트로 안내
        fallback = "질문을 제대로 처리하지 못했습니다. 문제 이해는 되셨나요? 이 문제를 어떻게 접근할지 풀이 전략을 말씀해 주세요."
        intro["problem_answer"] = intro.get("problem_answer") or ""
        state["tts_text"] = fallback
        state["await_human"] = True
        _mark_meta(meta, stage="intro", intro_flow_done = True)
        return state

    return state
