from typing import Any, Dict, List, Literal, TypedDict,Optional

CompletionLevel = Literal["COMPLETE", "POLISH", "NEEDS_WORK"]

class EvidenceCoachState(TypedDict, total=False):
    # request
    user_id: str
    video_id: str
    draft: str # 사용자 글
    
    # 임시
    video_summary: str
    
    normalized_draft:str # 사용자 글 정규화
    
    # judge output
    completion_level: CompletionLevel
    missing_slots: List[str]
    ambiguous_slots: List[str]
    lint: List[Dict[str, str]]        # {"tag": "...", "message": "..."}


    # coach output
    coach_output: str      # template/questions/one_line_feedback