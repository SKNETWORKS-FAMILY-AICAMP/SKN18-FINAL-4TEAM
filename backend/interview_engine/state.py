from typing import TypedDict, Literal, List, Dict, Any, Optional


# 1) 메타 / 공통 영역
class MetaState(TypedDict, total=False):
    session_id: str           # livecoding 세션 ID (redis 키에도 쓰는 값)
    user_id: str              # "sonju"
    stage: Literal[
        "intro",              # 문제 소개/전략 설명
        "coding",             # 코드 작성 중
        "finished"            # 세션 종료
    ]
    created_at: str           # ISO 문자열
    updated_at: str           # 매 노드 통과 시 갱신
    intro_flow_done: bool     # 한번 loop(질문/분류 플로우)

# 2) 인트로 단계 상태
class IntroState(TypedDict, total=False):
    intro_text: str             # 문제 읽어주는 멘트(smalltalk + 문제 설명)
    strategy_question: str      # 풀이 전략 질문
    user_strategy_answer: str   # 사용자의 전략 설명
    user_answer_class: Literal[
        "no_answer",               # 대답 안 함 / 너무 짧음
        "irrelevant",              # 문제와 상관없는 말
        "strategy",                # 풀이 전략 설명
        "problem_question",        # 문제에 대한 질문
        "unknown"
    ]
    user_question: Optional[str]   # 문제에 대해 되묻는 질문 텍스트
    problem_answer: Optional[str]   # 문제 관련 질문에 대한 답
    
    
    
class InterviewState(TypedDict, total=False):
    meta: MetaState
    problem_data: str
    intro: IntroState
    
    
    
    # HITL 용
    await_human: bool
    event_type: str
    

    tts_text:str
    stt_text:str
    

    user_question:str
    
    
    # 2번 agent
    submitted_code: str
    code: str
    language: str
    code_quality_rubric: str
    code_quality_summary: str
    code_quality_feedback: List[str]
    code_quality_score: float
    code_quality_error: str
    


    # 힌트 agent
    # - current_user_code: 현재 사용자의 전체 코드 (문자열)
    # - problem_algorithm_category: 예) "two_pointer", "dfs_bfs", "dp" 등
    # - hint_trigger: 힌트가 트리거된 방식 (버튼 클릭 / 정체 상태 감지 등)
    # - hint_text: LLM이 생성한 최신 힌트 내용 (사용자에게 그대로 보여줄 텍스트)
    # - hint_count: 지금까지 제공된 힌트 개수
    current_user_code: str
    problem_algorithm_category: str
    #   - "manual"       : 사용자가 힌트 버튼을 눌렀을 때
    #   - "auto_quality" : 코드 품질 평가 결과가 낮아서 자동으로 힌트를 줄 때
    hint_trigger: Literal["manual", "auto_quality"]
    hint_text: str
    hint_count: int
    
