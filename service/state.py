from typing import TypedDict, Literal, List, Dict, Any, Optional


class QARecord(TypedDict):
    turn_id: int
    focus: str                     # "problem_solving" | "collaboration" | "code_quality"
    question_text: str
    user_answer: str
    final_eval: Dict[str, Any]


class InterviewState(TypedDict):
    # 첫 정보
    session_id: int
    user_name: str
    problem_description: str  # 문제

    # problem_intro_and_strategy 결과
    problem_intro_text: str
    current_question_text: Optional[str]
    last_user_answer: str

    # HITL & 진행 단계
    phase: Literal[
        "init",           # 방금 세션 생성됨
        "strategy_intro", # 문제 설명 + 전략 질문 보여준 상태
        "live_loop",      # 일반 Q/A 루프
    ]
    await_human: Optional[Dict[str, Any]]

    # 실시간 정보
    latest_code: str
    qa_history: List[QARecord]
    qa_history_brief: str
    initial_strategy_eval: Optional[Dict[str, Any]]

    waiting_for_answer: bool
    next_node: Optional[str]       # supervisor가 지시한 다음 LLM 노드

    current_focus: Optional[str]   # "problem_solving" | "collaboration" | "code_quality"
    step_num: int

    # supervisor 용
    supervisor_mode: Literal["classify", "judge", "none"]
    last_raw_eval: Optional[Dict[str, Any]]
    last_final_eval: Optional[Dict[str, Any]]

    # 이번 호출에서 들어온 이벤트
    event_type: Literal["code_snapshot", "answer_submitted", "finish", "none"]
    event_payload: Dict[str, Any]