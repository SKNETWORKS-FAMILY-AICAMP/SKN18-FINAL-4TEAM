from chatbot.coach.state import CoachState
from chatbot.utils import LLM, _detect_period
from chatbot.coach.agents import exec_plan_agent

from chatbot.tools import (
    load_recent_outcome_logs,
    load_recent_coaching_logs,
    load_traits,
    load_preferences,
    get_recent_coding_reports)

def load_user_state_node(state: CoachState) -> CoachState:
    user_id = state["user_id"]

    try:
        outcomes = load_recent_outcome_logs.invoke({"user_id": user_id})
    except Exception:
        outcomes = []
    try:
        coaching_logs = load_recent_coaching_logs.invoke({"user_id": user_id})
    except Exception:
        coaching_logs = []
    try:
        traits = load_traits.invoke({"user_id": user_id})
    except Exception:
        traits = None
    try:
        preferences = load_preferences.invoke({"user_id": user_id})
    except Exception:
        preferences = None
    try:
        coding_reports = get_recent_coding_reports.invoke({"user_id":user_id})
    except Exception:
        coding_reports = []

    return {
        **state,
        "user_memory":{
            "outcomes": outcomes,
            "coaching_logs": coaching_logs,
            "traits":traits,
            "preferences":preferences,
            "coding_reports":coding_reports
        }

    }

def coach_classify_node(state: CoachState):
    """
    LLM-only Router:
        - EXEC_PLAN: 일일/주간 실행 계획 생성/업데이트
        - LONG_TERM_PLAN: 장기 로드맵/취준 전략/코테 준비 방법론
        - REVIEW: 회고/리뷰/조정/리밸런싱

    출력은 라벨 1개만.
    """
    message = (state.get("message") or "").strip()

    system_prompt = '''
        너는 개인화 학습 코치 시스템의 라우터다.
        사용자의 발화를 보고, 아래 3가지 중 하나로 분류하라.

        1) EXEC_PLAN: 일일/주간 실행 계획
        2) LONG_TERM_PLAN: 장기 목표·로드맵·전략
        3) REVIEW: 회고·리뷰·조정

        출력은 반드시 라벨 하나만.
        다른 설명은 하지 마라.
    '''.strip()

    try:
        resp = LLM.invoke([
            ("system", system_prompt),
            ("human",f"[사용자 발화] {message}"),
        ]).content.strip().upper()
    except Exception:
        resp = ""

    allowed = ["EXEC_PLAN", "LONG_TERM_PLAN", "REVIEW"]
    plan_kind = resp if resp in allowed else "unknown"


    return {
            **state,
            "plan_kind": plan_kind,
    }

def daily_weekly_node(state: CoachState) -> CoachState:
    """
    주간/일간 실행 계획을 제안한다.
    입력 컨텍스트: profile, user_memory(최근 성과/약점 등), message
    출력: daily_weekly_plan (LLM 텍스트)
    """
    profile = state.get("profile") or {}
    user_memory = state.get("user_memory") or {}
    session_summary = state.get("session_summary") or 10
    message = state.get("message") or ""
    period = _detect_period(message)
    weekly_hours = profile.get("weekly_hours")
    if period == "week":
        time_budget_minutes = int(weekly_hours * 60)
    else:
        daily_hours = max(1, int((weekly_hours) / 7))
        time_budget_minutes = int(daily_hours * 60)
        
    plan_result = exec_plan_agent.invoke({
        "message": message,
        "profile": profile,
        "user_memory": user_memory,
        "session_summary":session_summary,
        "time_budget_minutes": time_budget_minutes
    })
    return {**state, "daily_weekly_plan": plan_result}


def long_term_agent(state: CoachState) -> CoachState:
    """장기 로드맵/취준 전략 TODO 스텁."""
    return {**state, "agent_output": "long_term_agent not implemented yet"}


def review_agent(state: CoachState) -> CoachState:
    """회고/리뷰/조정 TODO 스텁."""
    return {**state, "agent_output": "review_agent not implemented yet"}


def normalize_to_actions(state: CoachState):
    return state
