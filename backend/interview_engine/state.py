from typing import TypedDict, Literal, List, Dict, Any, Optional

# 1) 메타 / 공통 영역
class MetaState(TypedDict, total=False):
    session_id: str           # livecoding 세션 ID (redis 키에도 쓰는 값)
    user_id: str              # "sonju"

# chapter1
class IntroState(TypedDict, total=False):
    meta: MetaState
    event_type:str
    problem_data: str           # 문제
    
    intro_text: str             # 문제 읽어주는 멘트(smalltalk + 문제 설명)
    user_strategy_answer: str   # 사용자의 전략 답변
    user_answer_class: Literal[
        "irrelevant",               # 대답 안 함 / 너무 짧음
        "strategy",                # 풀이 전략 설명
        "problem_question",        # 문제에 대한 질문
    ]
    user_question: Optional[str]   # 문제에 대해 되묻는 질문 텍스트
    problem_answer: Optional[str]   # 문제 관련 질문에 대한 답
    intro_flow_done: bool     # 한번 loop(질문/분류 플로우)
    
    tts_text : str
    stt_text : str

# chapter2
class CodingState(TypedDict, total=False):
    problem_data: str           # 문제 
    # 협업능력 평가(코드기준)
    collaboration_feedback: List[str]
    # Ruff 분석 결과 캐시
    ruff_issues: List[Dict[str, Any]]
    current_user_code: str
    problem_algorithm_category: str
    #   - "manual"       : 사용자가 힌트 버튼을 눌렀을 때
    #   - "auto_quality" : 코드 품질 평가 결과가 낮아서 자동으로 힌트를 줄 때
    hint_trigger: Literal["manual", "auto_quality"]
    hint_text: str
    hint_count: int
    
# chapter3
class EvalState(TypedDict, total=False):
    pass