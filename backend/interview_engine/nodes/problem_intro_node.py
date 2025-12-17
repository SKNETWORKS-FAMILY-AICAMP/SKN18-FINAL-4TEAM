from interview_engine.state import IntroState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def _get_problem_text(state: IntroState) -> str:
    """state.problem_data는 문자열만 기대한다."""
    return str(state.get("problem_data") or "")


from interview_engine.state import IntroState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def _get_problem_text(state: IntroState) -> str:
    """state.problem_data는 문자열만 기대한다."""
    return str(state.get("problem_data") or "")


def problem_intro_agent(state: IntroState) -> IntroState:
    """
    Step 1: Problem Introduction

    사용하는 state 필드:
        - problem_data: 문제 설명 텍스트 (str)
        - intro_text: 문제 성명 텍스트 (str)

    동작:
        - smalltalk + 문제 요약 + 풀이 전략 질문까지 포함된 TTS 멘트 생성
            - intro.intro_text에 저장
            - latency를 줄이기 위해 풀이 전략 질문은 공통지문으로 넣기 
            - tts_text 에 intro_text 저장
    """

    # 1) 문제 텍스트 가져오기
    problem: str = _get_problem_text(state)

    system_prompt = (
        "당신은 한국어로 말하는 코딩 테스트 음성 면접관입니다. "
        "지금은 문제 소개 단계이며, 인사 후 문제의 핵심만 자연스럽게 요약합니다. "
        "모든 문장은 '습니다' 또는 '니다'로 끝냅니다. "
        "마크다운과 특수기호는 쓰지 않습니다. "
        "변수명은 괄호로 풀어 말하고, 수식은 말로 풀어서 설명합니다."
    )

    human_prompt = (
        f"다음은 문제입니다:\n{problem}\n"
        "지원자에게 읽어줄 문제 소개 멘트를 3문장으로 작성하세요. "
        "간단한 인사 후 문제의 핵심 요구사항만 설명하세요."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = LLM.invoke(messages)
        raw = (getattr(response, "content", "") or "").strip()

        strategy_question = (
            "코드를 작성하기 전에 풀이 접근 방식과 사용할 알고리즘, 그리고 예상 시간 복잡도를 간단히 설명해 주세요."
        )
        intro_text = raw + "\n" + strategy_question
        state["intro_text"] = intro_text
        state["tts_text"] = intro_text

    except Exception:
        # 실패 시 state 그대로 반환
        return state

    return state