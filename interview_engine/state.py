from typing import TypedDict, Literal, List, Dict, Any, Optional

class InterviewState(TypedDict):
    # HITL 용
    await_human = bool
    event_type = Literal["init", 'strategy_submit']
    
    # 처음 input
    username = str
    
    # 문제 
    problem_description = str
    
    # 1번 agent
    problem_intro_error = str
    current_question_text =str
    
    # 2번 agent
    
    pass