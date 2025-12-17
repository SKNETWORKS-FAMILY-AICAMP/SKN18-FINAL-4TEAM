import json
from typing import Literal
from langchain_core.messages import SystemMessage, HumanMessage
from interview_engine.state import IntroState
from interview_engine.llm import LLM  # 아까 만든 싱글톤 LLM

AnswerClass = Literal["irrelevant", "strategy", "problem_question"]


def answer_classify_agent(state: IntroState) -> IntroState:
    user_text = (state.get("stt_text") or "").strip()
    non_strategy_count = int(state.get("intro_non_strategy_count") or 0)
    
    if not user_text:
        state["tts_text"] = "다시 대답해 주시겠어요?"
        return state
        
    problem_text = str(state.get("problem_data") or "").strip()
    system_prompt = """
        당신은 코딩 테스트 인터뷰 도우미입니다.
        사용자의 발화를 아래 카테고리 중 하나로 분류하십시오.

        카테고리:
        1. irrelevant:
            - 너무 짧아 의미를 파악할 수 없음.
            - 현재 문제/풀이 전략과 관련이 거의 없는 잡담, 일반 대화.

        3. strategy:
            - 문제 해결/풀이 전략에 대한 설명, 아이디어, 접근법.

        4. problem_question:
            - 문제 다시 설명, 조건/입출력/제약사항 등을 되묻는 질문.

        출력은 반드시 JSON 한 줄:
        {"answer_class": "<irrelevant|strategy|problem_question>"}
        """

    user_prompt = f"""
        [문제 지문]
        {problem_text}

        [사용자 발화]
        {user_text}
"""
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt),
    ]

    try:
        resp = LLM.invoke(messages)
        content = getattr(resp, "content", resp)

    except Exception:
        state["user_answer_class"] = "irrelevant"
        state["tts_text"] = "죄송합니다. 사용자의 응답을 처리하지 못했습니다. 다시 대답해 주세요."
        return state
        
        
    parsed = json.loads(content)
    answer_class: AnswerClass = parsed.get("answer_class", "irrelevant")
    if answer_class == "strategy":
        state["user_answer_class"] = answer_class
        state["user_strategy_answer"] = user_text
        state["intro_non_strategy_count"] = 0
        state["event_type"] = "coding_intro"
    else:
        state["user_answer_class"] = answer_class
        state["intro_non_strategy_count"] = non_strategy_count + 1
        if answer_class == "problem_question":
            state["user_question"] = user_text
        else:
            state["tts_text"] = "질문에 맞는 정확한 답변을 말해주세요."        

    return state

   
