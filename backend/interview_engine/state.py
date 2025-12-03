from typing import TypedDict, Literal, List, Dict, Any, Optional

class InterviewState(TypedDict, total=False):
    """
    Interview session state for langgraph.
    All fields are optional (total=False) to allow flexible state updates.
    """
    # HITL 용
    await_human: bool
    event_type: str
    
    # 처음 input
    user_name: str
    
    # 문제 
    problem_description: str
    
    # 1번 agent
    problem_intro_error: str
    current_question_text: str
    tts_first_audio_base64: str
    tts_audio_chunks: List[Dict[str, Any]]
    tts_error: str
    
    # 2번 agent
    submitted_code: str
    code: str
    language: str
    code_quality_rubric: str
    code_quality_summary: str
    code_quality_feedback: List[str]
    code_quality_score: float
    code_quality_error: str