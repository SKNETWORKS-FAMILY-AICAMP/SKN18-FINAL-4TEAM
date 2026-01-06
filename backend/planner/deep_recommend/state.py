from typing import Any, Dict, List, TypedDict

class UserProfile(TypedDict, total=False):
    teck_stack: List[str]
    desired_role: List[str]
    detailed_role:List[str]

class RecommendState(TypedDict, total=False):
    user_id:str
    user_profile: UserProfile
    growth_report: str
    needs_profile: Dict[str, Any]
    slots: List[Dict[str, Any]]
    candidates: List[Dict[str, Any]]
    final_plan: List[Dict[str, Any]]
