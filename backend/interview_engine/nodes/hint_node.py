from interview_engine.state import InterviewState
from langchain_core.messages import HumanMessage, SystemMessage
from langchain.chat_models import init_chat_model


def hint_agent(state: InterviewState) -> InterviewState:
    """
    Hint Agent입니다.

    사용하는 state 필드:
      - current_user_code: 현재 사용자 코드
      - problem_algorithm_category: 문제의 알고리즘 카테고리 (예: two_pointer, dfs_bfs, dp 등)
      - hint_trigger: "manual" | "auto_quality"
      - hint_count: 지금까지 제공한 힌트 개수

    동작:
      - manual 트리거: 사용자가 직접 버튼을 눌러 도움을 요청한 상황.
        → 현재 코드를 보고, "이렇게 생각해 보면 어떨까요? / 이렇게 구현해 보면 어떨까요?" 톤으로 방향+구현 힌트 제공.
      - auto_quality 트리거: 코드 품질이 낮거나 변화가 없어 시스템이 먼저 제안하는 상황.
        → "문제에 어려움이 있으신 것 같아 힌트를 드릴게요" 같은 한두 줄 공감 + 구체적인 개선 포인트 제안.
    """

    problem_algorithm_category = state.get("problem_algorithm_category", "")
    current_user_code = state.get("current_user_code", "")
    hint_trigger = state.get("hint_trigger", "manual")
    problem_description = state.get("problem_description", "")
    hint_count = int(state.get("hint_count", 0))

    if hint_trigger == "manual":
        trigger_description = (
            "사용자가 스스로 힌트 버튼을 눌러 도움을 요청한 상황입니다. "
            "현재 코드를 존중하면서 장점과 보완할 부분을 짚어 주고, "
            "'이렇게 생각해 보면 어떨까요?', '이렇게 구현해 보면 어떨까요?'와 같은 표현으로 "
            "다음에 시도해 볼 구체적인 방향을 제시하세요."
        )
    else:  # auto_quality
        trigger_description = (
            "코드 품질 평가 결과가 낮거나 일정 시간 동안 개선이 없어 시스템이 먼저 힌트를 제안하는 상황입니다. "
            "사용자가 문제를 어렵게 느끼고 있을 수 있으니, 먼저 공감과 격려 한두 문장을 말해 주고 "
            "'문제에 어려움이 있으신 것 같아 힌트를 드릴게요.'와 같은 문장을 포함한 뒤, "
            "어디서 막혀 있을 가능성이 높은지 추측하고 개선 방향을 알려 주세요."
        )

    system_prompt = (
        "당신은 라이브 코딩 인터뷰의 Hint Agent입니다.\n\n"
        f"- 문제 정보: {problem_description}\n"
        f"- 알고리즘 카테고리: {problem_algorithm_category or '알려지지 않음'}\n"
        f"- 힌트 트리거: {hint_trigger}\n"
        f"- 지금까지 제공된 힌트 개수: {hint_count}\n\n"
        "[상황 설명]\n"
        f"{trigger_description}\n\n"
        "[출력 규칙]\n"
        "1) 반드시 한국어로 작성하세요.\n"
        "2) 다음 요소를 모두 포함하세요:\n"
        "   - 현재 코드 상태에 대한 짧은 피드백 (잘한 점 1~2개 + 보완할 점 1~2개).\n"
        "   - '이렇게 생각해 보면 어떨까요?' 또는 비슷한 표현으로 시작하는 접근 아이디어.\n"
        "   - '이렇게 구현해 보면 어떨까요?' 또는 비슷한 표현으로 시작하는 구현 방향 힌트.\n"
        "3) 정답 전체 코드를 그대로 쓰지 말고, 핵심 아이디어와 구현 단계만 제안하세요.\n"
        "4) 마크다운 기호(**, *, -, • 등) 없이 순수 텍스트 한두 단락으로 작성하세요.\n"
        "5) 힌트를 많이 받은 상태(hint_count가 클수록)일수록 조금 더 구체적으로 돕되, "
        "   여전히 사용자가 스스로 코드를 완성하게 여지를 남기세요.\n"
    )

    human_prompt = (
        "[현재 사용자 코드]\n"
        f"{current_user_code or '코드가 비어 있습니다.'}\n\n"
        "위 코드를 기준으로, 지금 상황에 가장 도움이 될 만한 힌트를 작성해 주세요."
    )

    model = init_chat_model("gpt-5-nano")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt),
    ]

    try:
        response = model.invoke(messages)
        hint_text = (getattr(response, "content", "") or "").strip()
        if hint_text:
            state["hint_text"] = hint_text
            state["hint_count"] = hint_count + 1
    except Exception:
        # 실패 시 state는 그대로 둔다.
        return state

    return state