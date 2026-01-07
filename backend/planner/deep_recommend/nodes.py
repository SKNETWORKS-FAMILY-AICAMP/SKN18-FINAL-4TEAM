import json

from dotenv import load_dotenv
from .state import RecommendState
from .prompt import REPORT_ANALYZER_PROMPT, SLOT_PLANNER_PROMPT, VIDEO_SELECTOR_PROMPT
from .tools import _create_agent, video_search_tool, DEFAULT_MODEL_NAME
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from planner.deep_coach.utils import safe_json_parse
load_dotenv()




def report_analyzer(state: RecommendState) -> RecommendState:

    user_id = state.get("user_id", "")
    growth_report = state.get("growth_report", "")
    user_profile = state.get("user_profile", {})
    model = ChatOpenAI(model=DEFAULT_MODEL_NAME, temperature=0)
    prompt = f'''
        사용자 이름: {user_id}
        사용자 리포트: {growth_report}
        사용자 프로필: {user_profile}
    '''
    try:
        res = model.invoke(
            [
                SystemMessage(content=REPORT_ANALYZER_PROMPT),
                HumanMessage(content=prompt),
            ]
        )
        raw = getattr(res, "content", None) or str(res)
        parsed = safe_json_parse(raw)
        state["needs_profile"] = parsed.get("needs_profile")
    except Exception as exc:
        print(exc)

    return state


def slot_planner(state: RecommendState) -> RecommendState:
    """
    needs_profile를 받아 slots를 생성한다.
    """
    needs = state.get("needs_profile")
    agent = _create_agent(system_prompt=SLOT_PLANNER_PROMPT)
    prompt = f'[need_profile]: {needs}'
    try:
        res = agent.invoke({"messages": [{"role": "user", "content": prompt }]})
        raw = res["messages"][-1].content
        parsed = safe_json_parse(raw)
        state["slots"] = parsed.get("slots")

    except Exception as exc:
        print(exc)

    return state


def video_selector(state: RecommendState) -> RecommendState:

    needs = state.get("needs_profile")
    slots = state.get("slots")

    agent = _create_agent(system_prompt=VIDEO_SELECTOR_PROMPT, tools=[video_search_tool])
    user_msg = f'''
        [needs_profile] : {needs}
        [7일치 슬롯]: {slots}
    '''
    try:
        res = agent.invoke({"messages": [{"role": "user", "content": user_msg}]})
        raw = res["messages"][-1].content
        parsed = safe_json_parse(raw)
        candidates = parsed.get("candidates") or []
        state["candidates"] = candidates
        print(f"[video_selector] candidates={len(candidates)}", flush=True)
        print(f"[video_selector] candidates={candidates[0]}", flush=True)
    except Exception as exc:
        print(f"[video_selector] error: {exc}", flush=True)

    return state


def plan_builder(state: RecommendState) -> RecommendState:
    """
    candidates + slots를 조합해 final_plan을 결정한다(추가 LLM 호출 없이 결합).
    """
    candidates = state.get("candidates") or []
    slots = state.get("slots") or []

    cand_by_day = {c.get("day"): c for c in candidates if isinstance(c, dict)}
    final_plan = []

    for slot in slots:
        if not isinstance(slot, dict):
            continue
        day = slot.get("day")
        topic = slot.get("day_plan_topic")
        category = slot.get("category") or ""
        domain = slot.get("domain") or ""
        why_selected = slot.get("reason") 
        cand = cand_by_day.get(day) or {}
        video = cand.get("video") or {}
        raw_id = video.get("id")
        try:
            video_id = int(raw_id) if raw_id not in (None, "") else None
        except Exception:
            video_id = None
        video_url = video.get("video_url") or ""
        final_plan.append(
            {
                "day": day,
                "day_plan_topic": topic,
                "category": category,
                "domain": domain,
                "video_id": video_id,
                "video_url": video_url,
                "why_selected": why_selected,
            }
        )

    state["final_plan"] = final_plan
    print(f"[plan_builder] slots={len(slots)} final_plan={len(final_plan)}", flush=True)
    return state
