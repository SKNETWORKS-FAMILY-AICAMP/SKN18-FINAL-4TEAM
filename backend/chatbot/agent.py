from datetime import date
from typing import Any, Dict, Optional

from deepagents import create_deep_agent
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from memory import get_postgres_store, get_session_store, make_user_backend
from chatbot.tools import load_profile, upsert_profile
from chatbot.models import UserProfile
'''
필수 입력 값

{
  "request": {
    "session_id": "s_abc",
    "user_id": "u_123",
    "message": "이번 주 코테 준비 계획 짜줘",
    "intent": "plan"
  },
  "profile": {
    "role": "backend",
    "skill_level": "intermediate",
    "weekly_hours": 6,
  },
  "session_summary": {
    "dialog_summary": "사용자는 백엔드 취준생, 코테 실버 수준. 이번 주 준비 계획 요청.",
    "pending_question": null
  }
}
'''


REQUIRED_PROFILE_FIELDS = ("role", "skill_level", "weekly_hours")


class NextAction(BaseModel):
    title: str
    description: Optional[str] = None
    due: Optional[str] = Field(None, description="ISO 날짜(또는 시간 포함) 문자열")
    priority: Optional[str] = Field(None, description="low/medium/high 등")
    status: Optional[str] = Field("todo", description="todo/doing/done")


class WeeklyPlan(BaseModel):
    week_id: str
    week_goals: list[str]
    focus_areas: list[str]
    routines: dict[str, list[str]]
    next_actions: list[NextAction]


plan_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "너는 개발자 취업 준비생을 위한 한국어 코칭 에이전트야. "
            "입력된 프로필/요약/메시지를 기반으로 일주일 단위의 실천 가능한 계획을 JSON으로만 생성해. "
            "조직/형식 외의 설명 문장은 절대 섞지 마.",
        ),
        (
            "human",
            "프로필: {profile}\n"
            "세션 요약: {summary}\n"
            "사용자 메시지: {message}\n"
            "주차 시작일: {week_start}\n\n"
            "요구사항:\n"
            "1) week_id는 YYYY-WW 형태로 생성\n"
            "2) week_goals 2~4개\n"
            "3) focus_areas 3~5개\n"
            "4) routines는 요일별 리스트, 하루 3~5개 액션\n"
            "5) next_actions 3~5개(제목/설명/마감/우선순위/상태)\n"
            "JSON만 반환해.",
        ),
    ]
)

plan_parser = JsonOutputParser(pydantic_object=WeeklyPlan)


def coach_agent():
    """주간 계획/루틴/로드맵 담당 코칭 에이전트."""

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        request = context.get("request", {}) if context else {}
        profile = context.get("profile", {}) if context else {}
        summary = (context.get("session_summary") or {}).get("dialog_summary") or request.get("message", "")

        missing = [k for k in REQUIRED_PROFILE_FIELDS if not profile.get(k)]
        if missing:
            ask = f"프로필 보완이 필요해요. {', '.join(missing)} 값을 알려주시면 계획을 세울게요."
            return {"messages": [AIMessage(content=ask)], "agent": "coach", "context": context}

        week_start = date.today()
        inputs = {
            "profile": profile,
            "summary": summary,
            "message": request.get("message", ""),
            "week_start": week_start.isoformat(),
        }

        try:
            plan: WeeklyPlan = (plan_prompt | LLM | plan_parser).invoke(inputs)
            plan_dict = plan.model_dump()
        except Exception:
            fallback = "계획 생성 중 오류가 발생했어요. 잠시 후 다시 시도해주세요."
            return {"messages": [AIMessage(content=fallback)], "agent": "coach", "context": context}

        action_titles = ", ".join([a["title"] for a in plan_dict.get("next_actions", [])])
        reply = (
            f"이번 주 계획을 생성했어요 (주차: {plan_dict.get('week_id')}).\n"
            f"- 주간 목표: {', '.join(plan_dict.get('week_goals', []))}\n"
            f"- 포커스 영역: {', '.join(plan_dict.get('focus_areas', []))}\n"
            f"- 다음 액션: {action_titles}"
        )

        return {
            "messages": [AIMessage(content=reply)],
            "agent": "coach",
            "plan": plan_dict,
            "context": context,
        }

    return RunnableLambda(run)


def research_agent():
    """트렌드/출제 경향 리서치 에이전트 (임시 스텁)."""

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: 실제 리서치 로직/툴 호출 추가
        msg = "리서치 에이전트가 준비 중입니다."
        return {"agent": "research", "messages": [AIMessage(content=msg)], "context": context}

    return RunnableLambda(run)


def evidence_agent():
    """제출물 기반 코칭 에이전트 (임시 스텁)."""

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        # TODO: 실제 평가/루브릭 로직 추가
        msg = "증거 코칭 에이전트가 준비 중입니다."
        return {"agent": "evidence", "messages": [AIMessage(content=msg)], "context": context}

    return RunnableLambda(run)


LLM = ChatOpenAI(
                model="gpt-5-nano",
                reasoning_effort="high",        # 논리성 강화
            )

def build_context_pack(payload: Dict[str, Any]) -> Dict[str, Any]:
    """입력 payload에서 컨텍스트 팩을 추출/보정한다. 부족한 프로필/요약은 저장소에서 보강한다."""
    request = payload.get("request", {}) or {}
    profile = _hydrate_profile_from_db(request.get("user_id"), payload.get("profile", {}) or {})
    session_summary = payload.get("session_summary", {}) or {}
    # 세션 요약이 없으면 Redis에서 보강, 그래도 없으면 최근 메시지를 사용
    if not session_summary.get("dialog_summary"):
        session_id = request.get("session_id")
        if session_id:
            redis_summary = get_session_store().get_summary(session_id)
            if redis_summary:
                session_summary["dialog_summary"] = redis_summary
    if not session_summary.get("dialog_summary"):
        session_summary["dialog_summary"] = request.get("message")
    return {"request": request, "profile": profile, "session_summary": session_summary}


def missing_profile_fields(profile: Dict[str, Any]) -> list[str]:
    return [k for k in REQUIRED_PROFILE_FIELDS if not profile.get(k)]


def handle_request(payload: Dict[str, Any], store=None):
    """
    Context Pack을 구성하고, 필수 프로필 검증 후 메인 에이전트를 실행한다.
    프로필이 모자라면 질문 1개만 반환하고 서브에이전트 호출을 차단한다.
    """
    context_pack = build_context_pack(payload)
    missing = missing_profile_fields(context_pack["profile"])
    if missing:
        ask = f"프로필 보완이 필요해요. {', '.join(missing)} 값을 알려주시면 계획을 세울게요."
        return {"messages": [AIMessage(content=ask)], "agent": "main", "context": context_pack}

    user_id = context_pack["request"].get("user_id", "unknown")
    agent = create_main_agent(user_id=user_id, store=store)
    initial_msg = context_pack["request"].get("message", "")
    state = {
        **context_pack,
        "messages": [HumanMessage(content=initial_msg)],
    }
    return agent.invoke(state)


def _hydrate_profile_from_db(user_id: Optional[str], profile: Dict[str, Any]) -> Dict[str, Any]:
    """DB의 UserProfile 정보로 부족한 필드를 채운다."""
    if not user_id:
        return profile
    try:
        db_prof = UserProfile.objects.filter(user_id=user_id).first()
    except Exception:
        return profile
    if not db_prof:
        return profile

    merged = dict(profile)
    merged.setdefault("role", db_prof.role)
    merged.setdefault("skill_level", db_prof.skill_level)
    merged.setdefault("target_company", db_prof.target_company)
    merged.setdefault("due_date", db_prof.due_date.isoformat() if db_prof.due_date else None)
    merged.setdefault("weekly_hours", db_prof.weekly_hours)
    merged.setdefault("preferred_langs", db_prof.preferred_langs)
    return merged


subagents = [
    {
            "name": "coach_agent",
            "description": "주간 계획, 로드맵을 생성하는 전문가입니다. 계획 생성이 필요할 때 이 agent를 호출하세요.",
            "runnable": coach_agent()
    },
    {
            "name": "research_agent",
            "description": "데이터를 분석하고 인사이트를 도출하는 전문가입니다. 데이터 분석이 필요할 때 이 agent를 호출하세요.",
            "runnable": research_agent()
    },
    {
            "name": "evidence_agent",
            "description": "전문적인 보고서를 작성하는 전문가입니다. 문서 작성이 필요할 때 이 agent를 호출하세요.",
            "runnable": evidence_agent()
    }
]
def create_main_agent(user_id: str, store=None):
    """메인 에이전트 생성: 백엔드/체크포인터/툴/서브에이전트 연결"""

    MAIN_SYSTEM_PROMPT = f"""
    당신은 사용자 {user_id}를 위한 전용 개인화 메인 AI 코치입니다.
    모든 응답은 이 사용자의 맥락과 저장된 기억을 적극 활용해 일관성 있게 제공해야 합니다.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [단기 메모리: Redis /session/*]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - runtime: user_id, active_intent, evidence_type, stage, retry_count, last_verdict, updated_at
    - recent_msgs: 최근 N턴 대화 로그(LPUSH+LTRIM). 길이 초과 시 요약 후 교체.
    - dialog_summary: 최근 대화 요약/핵심 포인트
    - working_set/{{item_id}}: 처리 중 아티팩트(type, raw, normalized, status, source, hash)
    - graph_state: 그래프 중간 상태를 세션 동안만 유지
    TTL 기본 24h, 필요 시 요약/삭제로 크기를 억제한다.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [장기 메모리: Postgres /user/*, /memories/*]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - /user/profile: role, target_company, skill_level, preferred_langs, weekly_hours,
    - /user/weekly_plan/{{week_id}}: goals, routines, focus_areas, status
    - /user/research_briefs: topic, summary, actions, sources
    - /user/next_actions: title, description, due, priority, status
    - /user/outcome_logs: kind(PR/blog/ct 등), summary, link, score(optional)
    - /user/coaching_logs: artifact_id, findings, recommendations, rubric_scores
    - /memories/traits: strengths, weaknesses, patterns, confidence
    - /memories/preferences: tone_pref, detail_level, feedback_style
    - 코딩테스트 리포트: outcome/coaching 로그와 traits에 약점·오답 패턴을 저장해 계획/난이도 조정에 사용한다.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [승격/정리]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    - 세션 종료/주요 결과 생성 시: runtime/dialog_summary/working_set을 요약해 장기 저장소에 반영하고 Redis를 정리한다.
    - 저장된 정보가 있으면 재질문하지 말고 우선 활용한다.

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    [운영 규칙]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1) Context Pack 최소 스키마:
    - request: session_id, user_id, message, intent
    - profile: role, skill_level, weekly_hours
    - session_summary: dialog_summary(없으면 message)
    2) profile 필수 필드(role, skill_level, weekly_hours)가 없으면:
    - Sub Agent 호출 금지
    - 질문은 단 1개만 생성하여 보완 정보 요청
    3) Intent 라우팅:
    - plan     -> call_coach(context_pack)
    - research -> call_research(context_pack)
    - evidence -> call_evidence(context_pack)
    4) 저장 정책:
    - /session/* 은 Redis(short-term)
    - /user/*, /memories/* 은 Postgres(long-term)
    - Sub Agent는 저장하지 않으며 저장은 Main이 담당
"""

    return create_deep_agent(
        model= LLM,
        checkpointer=None,
        store=store,                # Postgres store (Django 설정 기반)
        backend=make_user_backend(user_id),            # CompositeBackend 권장
        subagents = subagents,
        # 세션 상태는 get_session_store()로 별도 관리하고, 여기에는 실제 툴만 등록한다.
        tools=[load_profile, upsert_profile],
        system_prompt=MAIN_SYSTEM_PROMPT,
    )

if __name__ == "__main__":
  user_id = "sonju"
  store = get_postgres_store()
  agent = create_main_agent(user_id=user_id, store=store)
