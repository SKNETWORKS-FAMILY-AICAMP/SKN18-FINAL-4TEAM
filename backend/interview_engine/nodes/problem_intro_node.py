from interview_engine.state import InterviewState
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model

def problem_intro_agent(state: InterviewState) -> InterviewState:
    """
    Step 1: Problem Introduction Agent입니다.

    사용하는 state 필드:
      - problem_data: 문제 정보 (title, description, constraints, io_examples 등)
      - user_question: 사용자가 질문한 내용 (없으면 None/빈 문자열 -> 소개 모드)
      - intro_done: 문제 소개가 이미 끝났는지 여부 (Boolean)

    동작:
      - Intro 모드 (user_question 없음):
        → 문제 정보를 바탕으로 지원자에게 문제를 브리핑하는 스크립트 생성.
        → TTS로 출력되므로 특수문자를 피하고 구어체로 변환.
      - Q&A 모드 (user_question 있음):
        → 사용자의 질문에 대해 답변. 정답 코드는 유출하지 않음.
        → 역시 TTS로 출력되므로 듣기 편한 문장으로 생성.
    """

    problem_data = state.get("problem_data", {})
    user_question = state.get("user_question", "")
    
    # 문제 정보 문자열로 정리
    title = problem_data.get("title", "제목 없음")
    desc = problem_data.get("description", "설명 없음")
    constraints = problem_data.get("constraints", "제한사항 없음")
    io_examples = problem_data.get("io_examples", "예시 없음")

    problem_context = (
        f"제목: {title}\n"
        f"설명: {desc}\n"
        f"제한사항: {constraints}\n"
        f"입출력 예시: {io_examples}"
    )

    # 트리거 판단: 질문이 있으면 Q&A, 없으면 초기 소개
    if user_question:
        mode = "qna"
        trigger_description = (
            "지원자가 문제 설명 후 질문을 한 상황입니다. "
            "질문의 의도를 파악하여 친절하게 답변해 주되, "
            "**절대 정답 코드나 핵심 알고리즘을 직접적으로 알려주지 마세요.** "
            "질문이 문제와 무관하다면 정중히 코딩 테스트에 집중해 달라고 요청하세요."
        )
    else:
        mode = "intro"
        trigger_description = (
            "지원자가 처음 입장하여 문제를 소개해야 하는 상황입니다. "
            "가벼운 인사와 함께 문제의 핵심 내용, 제한사항, 입출력 방식을 "
            "요약하여 브리핑하세요. "
            "마지막은 '준비되셨으면 시작해 주세요.'라는 멘트로 마무리하세요."
        )

    system_prompt = (
        "당신은 AI 기반 코딩 테스트의 전문 면접관입니다.\n"
        "당신의 답변은 **음성 합성(TTS)**을 통해 지원자에게 들리게 됩니다.\n\n"
        f"[문제 정보]\n{problem_context}\n\n"
        f"[현재 상황]\n{trigger_description}\n\n"
        "[출력 규칙 (매우 중요)]\n"
        "1) 반드시 한국어 구어체로 작성하세요. (예: '입니다', '합니다')\n"
        "2) **TTS 친화적 표현 사용:**\n"
        "   - 특수문자, 마크다운(```, *, #, - 등)은 절대 사용하지 마세요.\n"
        "   - 변수명이나 함수명은 발음대로 풀어서 쓰세요. (예: `user_id` -> 유저 아이디, `O(N)` -> 오 엔)\n"
        "   - 수식도 말로 풀어서 쓰세요. (예: `a <= 100` -> 에이는 백보다 작거나 같습니다)\n"
        "3) 문장은 너무 길지 않게 끊어서 작성하세요.\n"
    )

    if mode == "qna":
        human_prompt = (
            f"[지원자 질문]\n{user_question}\n\n"
            "위 질문에 대해 면접관으로서 답변 멘트를 작성해 주세요."
        )
    else:
        human_prompt = (
            "지원자가 입장했습니다. 문제 소개 멘트를 작성해 주세요."
        )

    model = init_chat_model("gpt-5-nano") 
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = model.invoke(messages)
        output_text = (getattr(response, "content", "") or "").strip()
        
        if output_text:
            # 결과 저장 (TTS로 보낼 텍스트)
            state["tts_text"] = output_text
            
            # 상태 업데이트 (소개 모드였다면 intro_done 처리)
            if mode == "intro":
                state["intro_done"] = True
                state["last_action"] = "introduced_problem"
            else:
                state["last_action"] = "answered_question"
                # 질문 처리가 끝났으므로 user_question 초기화 (선택 사항)
                state["user_question"] = "" 

    except Exception:
        # 실패 시 state 유지
        return state

    return state