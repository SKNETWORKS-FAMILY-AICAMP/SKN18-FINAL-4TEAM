import json
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from interview_engine.state import InterviewState
from interview_engine.llm import LLM  # 아까 만든 싱글톤 LLM
from interview_engine.nodes.problem_intro_node import _mark_meta

AnswerClass = Literal["no_answer", "irrelevant", "strategy", "problem_question", "unknown"]


def answer_classify_agent(state: InterviewState) -> InterviewState:
    # 이전 턴의 TTS 잔여물이 남지 않도록 초기화
    state["tts_text"] = ""
    user_text = (state.get("stt_text") or "").strip()
    problem_text = str(state.get("problem_data") or "").strip()

    intro = state.setdefault("intro", {})
    meta = state.setdefault("meta", {})

    # intro_flow_done=True이면 추가 분류 없이 바로 전략 답변으로 수집하고 한 번만 루프
    if meta.get("intro_flow_done"):
        intro["user_answer_class"] = "unknown"
        state["user_strategy_answer"] = user_text
        state["event_type"] = "idle"
        _mark_meta(meta, stage="coding")
        return state

    if not user_text:
        intro["user_answer_class"] = "no_answer"
        state["tts_text"] = "다시 질문에 대해 대답해 주세요."
        state["await_human"] = True
        return state

    system_prompt = """
        당신은 코딩 테스트 인터뷰 도우미입니다.
        사용자의 발화를 아래 카테고리 중 하나로 분류하십시오.

        카테고리:
        1. no_answer:
            - 대답을 하지 않았거나 너무 짧아 의미를 파악할 수 없음.

        2. irrelevant:
            - 현재 문제/풀이 전략과 관련이 거의 없는 잡담, 일반 대화.

        3. strategy:
            - 문제 해결/풀이 전략에 대한 설명, 아이디어, 접근법.

        4. problem_question:
            - 문제 다시 설명, 조건/입출력/제약사항 등을 되묻는 질문.

        5. unknown:
            - 위 어디에도 확실히 넣기 어려운 경우.

        출력은 반드시 JSON 한 줄:
        {"answer_class": "<no_answer|irrelevant|strategy|problem_question|unknown>"}
        """

    user_prompt = f"""
        [문제 지문]
        {problem_text}

        [사용자 발화]
        {user_text}
""".strip()

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    resp = LLM.invoke(messages)
    content = getattr(resp, "content", resp)

    try:
        parsed = json.loads(content)
        answer_class: AnswerClass = parsed.get("answer_class", "unknown")
    except Exception:
        intro["user_answer_class"] = "unknown"
        return state

    intro["user_answer_class"] = answer_class

    if answer_class in ("no_answer", "irrelevant"):
        state["tts_text"] = "다시 질문에 대해 대답해 주세요."
        state["await_human"] = True
    elif answer_class == "problem_question":
        intro["user_question"] = user_text
        state["event_type"] = "init"  # 문제 관련 Q&A로 라우팅
    else:
        # strategy / unknown → 일단 진행
        state["user_strategy_answer"] = user_text
        state["event_type"] = "idle"
        _mark_meta(meta, stage="coding")

    return state
