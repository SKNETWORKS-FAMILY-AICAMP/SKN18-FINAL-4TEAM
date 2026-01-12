from interview_engine.state import IntroState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import get_llm 


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
        "당신은 한국어로 말하는 코딩 테스트 음성 면접관입니다."
        "지금은 문제 소개 단계이며, 문제의 핵심만 간단하고 자연스럽게 요약합니다."
        "모든 문장은 '습니다' 또는 '니다'로 끝냅니다."
        "마크다운과 특수기호는 쓰지 않습니다."
        "변수명은 괄호로 풀어 말하고, 수식은 말로 풀어서 설명합니다."
        "부등호는 크거나 같다, 크다, 작다, 작거나 같다, 같다 처럼 풀어서 설명합니다."
        "숫자는 한국어로 풀어서 설명합니다."
        "마지막에 면접자에게 질문할때에는 '~하실건가요?', '~해주세요?' 와 같이 의문문 형태로 끝냅니다. "
    )

    human_prompt = (
        f"다음은 문제입니다:\n{problem}\n"
        "면접관으로서 문제의 핵심 요구사항만 **요약하여** 설명하세요.\n"
        "설명 마지막에 이 문제를 어떻게 풀어나갈 것인지 **(자료구조, 알고리즘, 시간/공간 복잡도)**등을 근거하여 면접자에게 질문하세요.\n"
        "절대 본인이 문제풀이 전략을 제시하지 마세요."
    )

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        model = get_llm("intro")
        response = model.invoke(messages)
        raw = (getattr(response, "content", "") or "").strip()
        intro_text = raw + "\n"
        state["intro_text"] = intro_text
        state["tts_text"] = intro_text

    except Exception:
        return state

    return state
