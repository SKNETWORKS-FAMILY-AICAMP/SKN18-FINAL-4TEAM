import os
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[3]  # project root
BACKEND_DIR = Path(__file__).resolve().parents[2]  # backend/
for p in (ROOT, BACKEND_DIR):
    if str(p) not in sys.path:
        sys.path.append(str(p))

# Django settings/bootstrap
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django
django.setup()

from deepagents import create_deep_agent
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda
from chatbot.main.memory import get_postgres_store, make_user_backend
from chatbot.coach.graph import coach_graph_flow
from chatbot.tools import (
    load_profile,
    upsert_profile
)
from chatbot.utils import LLM

"""
필수 입력 값 예시
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
    "preferred_langs": ["python"]
  },
  "session_summary": {
    "dialog_summary": "사용자는 백엔드 취준생, 코테 실버 수준. 이번 주 준비 계획 요청.",
    "pending_question": null
  }
}
"""


def research_agent():
    """트렌드/출제 경향 리서치 에이전트 (임시 스텁)."""

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        msg = "리서치 에이전트가 준비 중입니다."
        return {"agent": "research", "messages": [AIMessage(content=msg)], "context": context}

    return RunnableLambda(run)


def evidence_agent():
    """제출물 기반 코칭 에이전트 (임시 스텁)."""

    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        msg = "증거 코칭 에이전트가 준비 중입니다."
        return {"agent": "evidence", "messages": [AIMessage(content=msg)], "context": context}

    return RunnableLambda(run)


def coach_mode():
    workflow = coach_graph_flow()
    
    def run(context: Dict[str, Any]) -> Dict[str, Any]:
        if context is None or not isinstance(context, dict):
            raise ValueError("coach_mode 실행을 위해 context는(dict)가 필요합니다.")

        request = context.get("request")
        if request is None or not isinstance(request, dict):
            raise ValueError("coach_mode 실행을 위해 request(dict)가 필요합니다.")
        
        user_id = request["user_id"]
        message = request.get("message", "")
        session_id = request.get("session_id")
        session_summary = context.get("session_summary") or message

        profile = context.get("profile")
        if profile is None or not isinstance(profile, dict):
            raise ValueError("coach_mode 실행을 위해 profile(dict)가 필요합니다.")

        # 4) workflow 실행
        workflow_out = workflow.invoke({
            "user_id": user_id,
            "message": message,
            "session_id": session_id,
            "session_summary": session_summary,
            "profile": profile
        })

        return workflow_out

    return RunnableLambda(run)





subagents = [
    {
        "name": "coach_mode",
        "description": "주간 계획/루틴/로드맵 생성 및 일정/태스크 반영 코치",
        "runnable": coach_mode()
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
    [운영 규칙]
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    1) Context Pack 최소 스키마:
    - request: session_id, user_id, message, intent
    - profile: role, skill_level, weekly_hours, preferred_langs
    - session_summary: dialog_summary(없으면 message)
    2) profile 필수 필드(role, skill_level, weekly_hours, preferred_langs)가 없으면:
    - Sub Agent 호출 금지
    - 질문은 단 1개만 생성하여 보완 정보 요청
    3) Intent 라우팅:
    - plan     -> coach_mode(context_pack)
    - research -> research_agent(context_pack)
    - evidence -> evidence_agent(context_pack)
    4) 저장 정책:
    - /session/* 은 Redis(short-term)
    - /user/*, /memories/* 은 Postgres(long-term)
    - Sub Agent는 저장하지 않으며 저장은 Main이 담당
"""

    return create_deep_agent(
        model=LLM,
        checkpointer=None,
        store=store,  # Postgres store (Django 설정 기반)
        backend=make_user_backend(user_id),  # CompositeBackend 권장
        subagents=subagents,
        tools=[load_profile, upsert_profile],
        system_prompt=MAIN_SYSTEM_PROMPT,
    )


if __name__ == "__main__":
    user_id = "sonju"
    store = get_postgres_store()
    agent = create_main_agent(user_id=user_id, store=store)
    res = agent.invoke({
    "request": {"session_id": "s1", "user_id": "sonju", "message": "이번주 코테 준비 계획 짜줘", "intent": "plan"},
    "profile": {"role": "backend", "skill_level": "intermediate", "weekly_hours": 6, "preferred_langs": ["python"]},
    "session_summary": "백엔드 취준생, 코테 준비"
    })
    print(res)
