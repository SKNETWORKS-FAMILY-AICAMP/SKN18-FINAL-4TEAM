from typing import TypedDict, List, Dict, Any, Optional


class UserMemoryState(TypedDict, total=False):
    traits: Dict[str, Any]
    preferences: Dict[str, Any]
    outcomes: List[Dict[str, Any]]
    coaching_logs: List[Dict[str, Any]]
    coding_reports: List[Dict[str, Any]]

class CoachState(TypedDict, total=False):
    user_id: str
    session_id: str
    message: str
    session_summary:str
    profile: Dict[str, Any]
    user_memory: UserMemoryState
    plan_kind: str

    
