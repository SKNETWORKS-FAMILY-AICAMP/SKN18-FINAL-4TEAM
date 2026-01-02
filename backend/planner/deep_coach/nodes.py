import json
from typing import Any, Dict
from utils import _normalize_for_judge, _calc_tool_level,_choose_lenient
from state import EvidenceCoachState
from agents import create_judge_agent, create_feedback_agent
from utils import safe_json_parse
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

    # user 메시지: 영상 요약 + 사용자 요약
    user_prompt = f"[영상 요약]\\n{video_summary}\\n\\n[사용자 요약]\\n{draft}"

    # 메인 judge 에이전트 생성
    agent = create_judge_agent()
    parsed: Dict[str, Any] = {}
    try:
        res = agent.invoke({"messages": [{"role": "user", "content": user_prompt}]})
        raw = res["messages"][-1].content
        parsed = safe_json_parse(raw)
    except Exception as e:
        print(f"agent 호출 오류: {e}")

    missing = parsed.get("missing_slots", [])
    lint = parsed.get("lint", [])

    tool_level = _calc_tool_level(missing, lint)
    llm_level = parsed.get("completion_level")

    state["completion_level"] = _choose_lenient(llm_level, tool_level)
    state["missing_slots"] = missing
    # coach 단계에서 부분 반영/모호 슬롯 활용
    state["ambiguous_slots"] = parsed.get("ambiguous_slots", parsed.get("ambiguous", []))
    state["lint"] = lint
    return state

def final_feedback_agent_node(state: EvidenceCoachState )-> EvidenceCoachState:
    """
    judge 결과와 원문을 받아 인라인 코멘트 및 정돈본을 생성한다.
    """
    video_summary = state.get("video_summary", "")
    draft = state.get("draft")
    missing = state.get("missing_slots", [])
    ambiguous = state.get("ambiguous_slots", [])
    lint = state.get("lint", [])
    completion = state.get("completion_level", "NEEDS_WORK")

    agent = create_feedback_agent()
    try:
        res = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"""
                            [video_summary]
                            {video_summary}

                            [draft]
                            {draft}

                            [completion_level]{completion}
                            [missing_slots]{missing}
                            [ambiguous_slots]{ambiguous}
                            [lint]{lint}
                        """,
                    }]
            }
        )
        raw = res["messages"][-1].content
        parsed = safe_json_parse(raw)   
    except Exception as e:
        print(f"agent 호출 오류: {e}")

    state["coach_output"] = parsed.get("annotated_draft")
    return state
