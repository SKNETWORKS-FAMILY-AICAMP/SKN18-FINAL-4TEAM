from interview_engine.state import InterviewState

def route_loop(state:InterviewState) -> str:
    etype = state.get("event_type")
    
    if state.get("await_human"):
        return  "idle"  
    
    if etype == "init":
        return  "problem_intro_agent"
    elif etype == "strategy_submit":
        return  "answer_classify_agent"
        
    
    return 'idle'