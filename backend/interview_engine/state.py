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
class InterviewState(TypedDict, total=False):
    # 1. 핵심 컨텍스트 (Redis Shared Data)
    current_user_code: str          # 현재 에디터 코드
    problem_description: str        # 문제 지문
    user_algorithm_category: str    # Step1에서 사용자가 선택한 알고리즘 (예: Greedy)
    real_algorithm_category: str    # 실제 문제 알고리즘 (예: DP)
    test_cases: str                 # 테스트 케이스 정보 (JSON 문자열 등)
    
    # 2. 힌트 제어 플래그
    hint_trigger: str               # "manual" (버튼) | "auto_quality" (자동 감지)
    hint_count: int                 # 현재까지 사용한 힌트 횟수
    
    # 3. 출력 데이터 (업데이트 대상)
    hint_text: str                  # 생성된 힌트 내용
    conversation_log: List[Any]     # 대화 내역 (질문 에이전트와 공유)
