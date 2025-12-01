from interview_engine.state import InterviewState

def route_loop(state:InterviewState) -> str:
    next_node = ""
    etype = state.get("event_type")
    
    if state.get("await_human"):
        return  "idle"  
    
    if etype == "init":
        next_node = "problem_intro_agent"
    elif etype == "strategy_submit":
        next_node = "answer_classify_agent"
        
    
    return next_node


