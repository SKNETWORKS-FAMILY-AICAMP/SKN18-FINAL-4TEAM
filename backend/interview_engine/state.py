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
    