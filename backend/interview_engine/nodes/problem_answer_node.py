from interview_engine.state import IntroState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import get_llm 
from interview_engine.nodes.problem_intro_node import _get_problem_text

def problem_answer_agent(state: IntroState) -> IntroState:
    """
    Step 2: Q&A Agent

    사용하는 state 필드:
        - problem_data: 문제 설명 텍스트 (str)
        - user_question: 사용자가 말한 질문 텍스트 (str)

    동작:
        - Q&A 모드 (user_question 있음):
            - 문제 관련 질문에 대한 답변 멘트 생성
            - problem_answer에 저장
    """

    # 1) 문제/질문 텍스트 가져오기
    problem: str = _get_problem_text(state)
    user_question:str = state.get("user_question")

    # ─────────────────────────────────────────
    # Q&A 모드: 문제 관련 질문에 대한 답변 생성
    # ─────────────────────────────────────────
    system_prompt_qna = (
    "당신은 AI 기반 코딩 테스트의 음성 면접관입니다.\n"
    "당신의 출력은 음성 합성(TTS)을 통해 지원자에게 전달됩니다.\n\n"
    "지원자가 방금 코딩 테스트 문제에 대해 질문을 했습니다.\n"
    "질문에 대해 친절하고 명확하게 답변해 주세요.\n\n"
    "[출력 규칙]\n"
    "1) 모든 문장은 '습니다', '니다'로 끝나야 합니다.\n"
    "2) TTS 친화적 표현만 사용하세요. Markdown 기호나 복잡한 수식은 피하세요.\n"
    "3) 문장은 너무 길지 않게, 짧고 명확하게 작성해 주세요.\n"
)

    human_prompt_qna = (
    f"[문제 정보]\n{problem}\n\n"
    f"[지원자 질문]\n{user_question}\n\n"
    "위 질문에 대해 코딩 테스트 면접관의 입장에서 답변을 작성해 주세요."
    )

    messages_qna = [
        SystemMessage(content=system_prompt_qna),
        HumanMessage(content=human_prompt_qna),
    ]

    try:
        print("[LLM][problem_answer_agent] system_prompt_qna:", system_prompt_qna, flush=True)
        print("[LLM][problem_answer_agent] human_prompt_qna:", human_prompt_qna, flush=True)
        
        model = get_llm("default")
        response = model.invoke(messages_qna)
        content = (getattr(response, "content", "") or "").strip()
        if not content:
            state["tts_text"] = (
                "질문에 대한 답변을 준비하지 못했습니다. "
                "다시 한 번 말씀해 주시겠습니까?"
            )
            return state

        requestion_text = (
            "문제 이해는 되셨습니까? "
            "그렇다면 이 문제를 어떻게 접근하실지, 풀이 전략을 설명해 주시겠습니까?"
        )
        # Q&A 답변을 저장
        state["problem_answer"] = content
        state["tts_text"]= content + "\n\n" + requestion_text

    except Exception:
        # LLM 실패 시에도 플로우가 끊기지 않도록 기본 멘트로 안내
        fallback = (
            "질문을 제대로 처리하지 못했습니다. "
            "번거로우시겠지만 다시 한 번 말씀해 주시겠습니까?"
        )
        state["tts_text"] = fallback
        return state

    return state
