from interview_engine.state import InterviewState


def route_loop(state: InterviewState) -> str:
    """
    event_type와 await_human 플래그를 기반으로 다음 노드 결정.
    """
    if state.get("await_human"):
        return "idle"

    etype = (state.get("event_type") or "").strip()

    routes = {
        "init": "problem_intro_agent",          # 문제 소개/Q&A
        "strategy_submit": "answer_classify_agent",  # STT로 받은 답변 분류
        "code_init": "collaboration_eval_agent",      # 코드 평가 시작
        "hint_request": "hint_agent",           # 힌트 요청
    }

    return routes.get(etype, "idle")

