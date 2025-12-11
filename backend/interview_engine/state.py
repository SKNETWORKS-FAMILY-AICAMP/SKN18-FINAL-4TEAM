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
    # 코딩 챕터에서 스트림으로 관리되는 상태 필드 집합
    meta: MetaState                 # 세션/유저 식별용 메타 정보
    event_type: str                 # 현재 이벤트 유형 (coding, feedback 등)
    language: str                   # 사용 언어 (python/js 등)
    question: str                   # 현재 질문 텍스트
    last_question_text: str         # 마지막으로 노출한 질문 텍스트(반복 방지용)
    code: str                       # 실시간 코드 스냅샷

    # 코드 비교/진행도 판단을 위한 보조 필드들
    starter_code: str               # 초기 제공 코드
    prev_code: str                  # 직전 코드 스냅샷
    snapshot_index: int             # 현재 스냅샷 인덱스
    last_snapshot_index: int        # 마지막 스냅샷 인덱스(프론트 동기화용)
    code_quality_feedback: str      # 코드 품질 피드백 메시지
    collaboration_feedback: str     # 협업/커뮤니케이션 관련 피드백
    question_cnt: int               # 질문/피드백 횟수 카운트
    tts_text: str                   # TTS로 읽을 텍스트
    stt_text: str                   # STT로 받은 텍스트

    # 힌트 관련 필드
    # 1. 핵심 컨텍스트 (Redis Shared Data)
    current_user_code: str          # 현재 에디터 코드
    problem_description: str        # 문제 지문
    user_algorithm_category: str    # Step1에서 사용자가 선택한 알고리즘 (예: Greedy)
    real_algorithm_category: str    # 실제 문제 알고리즘 (예: DP)
    test_cases: str                 # 테스트 케이스 정보 (JSON 문자열 등)
    # 2. 힌트 에이전트 상태 관리 필드
    hint_trigger: str               # "manual" (버튼)
    hint_count: int                 # 사용한 힌트 횟수
    hint_text: str                  # 생성된 힌트 내용
    conversation_log: List[Any]     # 대화 내역 (질문 에이전트와 공유)
    is_done: bool                   # 코딩 챕터 종료 여부
