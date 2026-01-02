from typing import Any, Dict, List, Literal, TypedDict,Optional

CompletionLevel = Literal["COMPLETE", "POLISH", "NEEDS_WORK"]
CoachMode = Literal["FINAL_REVIEW", "POLISH", "RESTRUCTURE"]

class EvidenceCoachState(TypedDict, total=False):
    # request
    user_id: str
    session_id: str
    week_id: str
    plan_item_id: str
    
    
    
    draft: str # 사용자 글
    normalized_draft:str # 사용자 글 정규화
    
    
    
    # plan context
    plan_item: Dict[str, Any]         # video_id, topic, duration, 목표 등
    last_pending_slots: List[str]     # (Redis/DB에서 로드) 이전 라운드 요구 슬롯
    round: int                        # item별 라운드 카운트

    # judge output
    completion_level: CompletionLevel
    missing_slots: List[str]
    lint: List[Dict[str, str]]        # {"tag": "...", "message": "..."}
    confidence: float

    # route
    mode: CoachMode

    # coach output
    coach_output: Dict[str, Any]      # template/questions/one_line_feedback
    pending_slots: List[str]

    # persistence
    evidence_id: Optional[str]