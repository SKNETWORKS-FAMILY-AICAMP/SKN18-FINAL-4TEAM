from typing import TypedDict, List, Optional

class PlanState(TypedDict):
    # [입력]
    # user_weakness: str
    duration: int
    growth_report_content: str
    
    # [작업 메모리]
    curriculum: List[dict]       # 계획 (날짜, 주제, 검색어)
    final_schedule: List[dict]   # 결과 (영상 정보 포함)
    
    # [제어 상태]
    retry_count: int             # 재시도 횟수
    validation_feedback: str     # 실패 원인 (Validator의 지적)
    incomplete_days: List[int]   # 다시 검색해야 할 날짜들