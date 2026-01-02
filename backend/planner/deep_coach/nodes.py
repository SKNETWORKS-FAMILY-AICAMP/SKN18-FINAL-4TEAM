import json
from typing import Any, Dict, List, Optional, TypedDict
from utils import _normalize_for_judge
from state import EvidenceCoachState
from agents import create_judge_agent

# ---------- node ----------
def evidence_ingest_node(state: EvidenceCoachState) -> EvidenceCoachState:
    ''' 
    1. REDIS round 조회 및 저장
    2. 사용자의 글 정규화 
    '''
    # 1) normalize draft
    draft = _normalize_for_judge(state.get("draft", ""))
    state["normalized_draft"] = draft
    
    return state

def judge_progress_agent_node(state: EvidenceCoachState )-> EvidenceCoachState:
    """
    1. 입력: 영상 요약(video_summary), 정규화된 사용자 글(normalized_draft)
    2. slot-matcher + lint-checker + judge_calc_tool 결과로 진행도 판단
    """
    video_summary = state.get("video_summary")
    draft = state.get("normalized_draft", "")

    # 메인 judge 에이전트 생성
    agent = create_judge_agent()

    # user 메시지: 영상 요약 + 사용자 요약
    user_prompt = f"[영상 요약]\\n{video_summary}\\n\\n[사용자 요약]\\n{draft}"

    try:
        res = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
        parsed = res.get("structured_response")
        if not parsed:
            # deepagent 표준 응답이 아닐 경우, 마지막 메시지에서 JSON 추출 시도
            last = (res.get("messages") or [])[-1] if isinstance(res, dict) else None
            content = getattr(last, "content", None) if last else None
            if content:
                parsed = json.loads(content)
        if not isinstance(parsed, dict):
            parsed = {}
    except Exception:
        parsed = {}

    state["completion_level"] = parsed.get("completion_level", "NEEDS_WORK")
    state["missing_slots"] = parsed.get("missing_slots", [])
    state["lint"] = parsed.get("lint", [])
    return state


def final_feedback_agent_node(state: EvidenceCoachState )-> EvidenceCoachState:
    pass


