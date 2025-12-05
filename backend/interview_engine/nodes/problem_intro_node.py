from interview_engine.state import InterviewState
from langchain_core.messages import HumanMessage, SystemMessage
from interview_engine.llm import LLM 


def problem_intro_agent(state: InterviewState) -> InterviewState:
    """
    Step 1: Problem Introduction Agent

    예상으로 사용하는 state 필드:
      - problem_data: 문제 정보 (problem, difficulty, category, language, function_name, starter_code, test_cases 등)
      - user_question: 사용자 질문 텍스트 (없으면 None/빈문자열 -> 소개 모드)
      - intro_done: 문제 소개가 완료되었는지 여부 (Boolean)

    동작:
      - Intro 모드 (user_question 없음):
        랜덤 문제 정보를 바탕으로 사용자에게 문제를 브리핑하고 TTS로 출력하기 쉬운 형태로 변환.
        ➜ 문제 설명 + 풀이 접근 전략에 대한 질문까지 포함.
      - Q&A 모드 (user_question 있음):
        사용자의 질문에 답변. 필요 시 TTS로도 출력하기 좋은 문장 형태로 변환.
    """

    problem_data = state.get("problem_data", "")
    user_question = state.get("user_question", "")

    problem_context = (
        f"문제: {problem_data}\n"
    )

    # 모드 판단: 질문이 있으면 Q&A, 없으면 초기 소개
    if user_question:
        mode = "qna"
        trigger_description = (
            "사용자가 문제 설명 관련 질문을 한 상황입니다. "
            "질문에 답하도록 요청하며, **코드나 공식은 직접 적어줄 것을 명시** "
            "질문이 문제와 무관하다면 코딩 테스트와 관련한 것인지 확인해달라 요청해주세요."
        )
    else:
        mode = "intro"
        trigger_description = (
            "사용자가 처음 등장하여 문제를 소개해야 하는 상황입니다. "
            "간결한 말투로 문제를 요약, 제한사항, 입출력 방식을 "
            "알려주며 브리핑하세요. "
            "지원자에게 사용할 알고리즘, 자료 구조, 시간 복잡도 등을 포함한 풀이 전략을 말로 설명해 달라는 질문을 던져 주세요. "
        )

    system_prompt = (
        "당신은 AI 기반 코딩 테스트의 음성 면접관입니다.\n"
        "당신의 출력은 **음성 합성(TTS)**을 통해 전달됩니다.\n\n"
        "처음 한두문장의 사용자 긴장을 풀어주는 말을 해주세요\n\n"
        f"[문제 정보]\n{problem_context}\n\n"
        f"[현재 상황]\n{trigger_description}\n\n"
        "[출력 규칙 (매우 중요)]\n"
        "1) 반듯하고 한국어 문장으로 완성하세요 (끝은 '습니다', '니다').\n"
        "2) **TTS 친화적 표현 사용:**\n"
        "   - 화살표, markdown(```, *, #, - 등)이나 특수문자는 쓰지 말아주세요.\n"
        "   - 변수명이나 함수명 발음이 필요한 경우 괄호로 읽기 쉽게 풀어주세요 (예: user_id -> 유저 아이디, O(N) -> 오 엔).\n"
        "   - 숫자나 조건은 말로 풀어주세요 (예: a <= 100 -> 에이가 백 이하입니다).\n"
        "3) 문장은 너무 길지 않게 짧게 써주세요.\n"
    )

    if mode == "qna":
        human_prompt = (
            f"[사용자 질문]\n{user_question}\n\n"
            "이 질문에 대해 면접관으로서 답변을 작성해주세요"
        )
    else:
        human_prompt = (
            "사용자가 등장했습니다. 문제 소개 멘트를 작성해주세요"
        )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = LLM.invoke(messages)
        content  = (getattr(response, "content", "") or "").strip()
        state["tts_text"] = content
  
        # 상태 업데이트 (소개 모드라면 intro_done 처리)
        if mode == "intro":
            state["await_human"] = True
            state['phase'] = state.get("event_type") # 상태 업데이트 
        else:
            state["await_human"] = True 

    except Exception:
        # 실패 시 state 그대로 반환
        return state

    return state