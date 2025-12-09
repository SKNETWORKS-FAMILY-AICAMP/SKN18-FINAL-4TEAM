from backend.interview_engine.state import IntroState


def chap1_answer_route(state: IntroState) -> str:
    user_answer_class = (state.get("user_answer_class") or "").strip()
    
    return {
        "irrelevant": "finish",
        "strategy": "finish",
        "problem_question": "problem_answer_agent",
    }.get(user_answer_class, "finish")  # 기본값
    
    
def chap1_main_condition(state: IntroState) -> str:
    etype = (state.get("user_answer_class") or "").strip()
    
    return {
        "init": "problem_intro_agent",
        "strategy_submit": "answer_classify_agent",
    }.get(etype, "idle")  # 기본값
