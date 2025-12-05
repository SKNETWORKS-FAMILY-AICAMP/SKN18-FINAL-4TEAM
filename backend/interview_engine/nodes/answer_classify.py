import json
from typing import Literal

from langchain_core.messages import SystemMessage, HumanMessage
from interview_engine.state import InterviewState
from interview_engine.llm import LLM  # 아까 만든 싱글톤 LLM


AnswerClass = Literal["UNRELATED", "RELATED_ANSWER", "PROBLEM_QUESTION"]


def answer_classify_agent(state: InterviewState) -> InterviewState:
    user_text = (state.get("stt_text") or "").strip()

    problem_text = ""
    if isinstance(state.get("problem_data"), dict):
        problem_text = str(state["problem_data"].get("problem", "")).strip()

    if not user_text:
        # 사용자가 아무 말도 안했으면 그냥 관련 없음으로 처리
        state["answer_class"] = "UNRELATED"
        state["tts_text"] = "다시 질문에 대해 대답해주세요."
        return state

    system_prompt = """
        당신은 면접/코딩 인터뷰 도우미입니다.
        사용자의 발화를 아래 세 가지 카테고리 중 하나로 분류하십시오.

        카테고리:
        1. UNRELATED: 
            -  현재 문제나 문제에 대한 풀이전략을 물어보는 질의와 거의 상관없는 잡담/일반 대화/의미 없는 대답
            - 예: "점심 먹었어요", "잘 모르겠어요", "아무거나요" 등
            
        2. RELATED_ANSWER:
            - 현재 문제나 문제에 대한 풀이전략을 물어보는 질의에 대해 사용자가 "답변"을 하고 있는 경우
            - 자신의 생각, 해결 아이디어, 코드를 어떻게 짤지 설명하는 내용 등
            
        - PROBLEM_QUESTION:
            - 사용자가 문제에 대해 "되묻는" 경우
            - 문제 조건/입출력/제약사항/용어를 다시 묻는 형태
            - 예: "입력 N의 최대 크기가 어떻게 되나요?", "중복 허용인가요?"

        출력 형식은 반드시 아래 JSON 형식의 한 줄 문자열로만 반환하십시오.

        {"answer_class": "<UNRELATED|RELATED_ANSWER|PROBLEM_QUESTION>"} 
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
        answer_class = parsed.get("answer_class", "UNRELATED")
        state["answer_class"] = answer_class
        
    except Exception:
        return state

    if answer_class == "UNRELATED":
        state["tts_text"] = "다시 질문에 대해 대답해 주세요"
        state["await_human"] = True
        
    elif answer_class == "PROBLEM_QUESTION":
        state["event_type"] = "init"
        state["user_question"] = user_text
    
    else:
        state["event_type"] = "idle"

    return state