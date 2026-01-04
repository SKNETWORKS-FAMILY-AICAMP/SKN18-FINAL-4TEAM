from typing import Any, Dict, List

from deepagents import create_deep_agent
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

DEFAULT_MODEL_NAME = "gpt-4o-mini"


@tool
def video_search_tool(query: str) -> Dict[str, Any]:
    """
    RecommendedVideo 모델(recommended_videos 테이블)을 조회해 요약/카테고리/도메인 기반 후보를 찾는다.
    - summary에 대한 icontains 검색
    - ArrayField(category)에도 부분 일치 검색 시도
    """
    try:
        from django.apps import apps
        from django.db.models import Q
    except Exception as exc:  # pragma: no cover - Django 미초기화 시
        return {"query": query, "results": [], "note": f"Django import 실패: {exc}"}

    model = apps.get_model(app_label="planner", model_name="RecommendedVideo")
    if not model:
        return {"query": query, "results": [], "note": "planner.RecommendedVideo 모델을 찾을 수 없습니다"}

    try:
        qs = model.objects.all()
        if query:
            qs = qs.filter(Q(summary__icontains=query) | Q(category__icontains=query) | Q(domain__icontains=query))
        qs = qs.order_by("-created_at")[:10]

        results = [
            {
                "id": obj.id,
                "video_url": getattr(obj, "video_url", None),
                "summary": getattr(obj, "summary", None),
                "category": getattr(obj, "category", None),
                "code_lang": getattr(obj, "code_lang", None),
                "domain": getattr(obj, "domain", None),
                "created_at": getattr(obj, "created_at", None).isoformat() if getattr(obj, "created_at", None) else None,
            }
            for obj in qs
        ]
    except Exception as exc:  # pragma: no cover - DB 접근 실패 시
        return {"query": query, "results": [], "note": f"DB 조회 실패: {exc}"}

    return {"query": query, "results": results, "note": "RecommendedVideo 조회 결과"}


@tool
def validate_plan_tool(plan: List[Dict[str, Any]]) -> Dict[str, Any]:
    """7일 플랜 품질을 검증한다."""
    issues: List[str] = []
    plan = plan or []

    if len(plan) != 7:
        issues.append("slots_count: 7일 플랜이 아닙니다")

    topics = [item.get("topic") for item in plan if isinstance(item, dict)]
    urls = [item.get("video_url") for item in plan if isinstance(item, dict)]

    def _find_dupes(values: List[Any]) -> List[str]:
        seen = set()
        dupes = set()
        for val in values:
            if not val:
                continue
            if val in seen:
                dupes.add(val)
            else:
                seen.add(val)
        return sorted(list(dupes))

    dup_topics = _find_dupes(topics)
    dup_urls = _find_dupes(urls)
    if dup_topics:
        issues.append(f"topic_duplication: {dup_topics}")
    if dup_urls:
        issues.append(f"video_url_duplication: {dup_urls}")

    for idx, item in enumerate(plan):
        if not isinstance(item, dict):
            issues.append(f"slot_{idx+1}: invalid item")
            continue

        diff = item.get("difficulty")
        if diff is None:
            issues.append(f"slot_{idx+1}: difficulty 누락")
        else:
            try:
                diff_val = int(diff)
                if diff_val < 1 or diff_val > 5:
                    issues.append(f"slot_{idx+1}: difficulty 범위(1~5) 위반")
            except Exception:
                issues.append(f"slot_{idx+1}: difficulty 숫자 아님")

        if not item.get("topic"):
            issues.append(f"slot_{idx+1}: topic 누락")
        if not item.get("video_title"):
            issues.append(f"slot_{idx+1}: video_title 누락")
        if not item.get("video_url"):
            issues.append(f"slot_{idx+1}: video_url 누락")

        criteria = item.get("success_criteria") or []
        if not criteria or not isinstance(criteria, list):
            issues.append(f"slot_{idx+1}: success_criteria 누락")



    return {"ok": len(issues) == 0, "issues": issues}


REPORT_ANALYZER_PROMPT = """
너는 ReportAnalyzerAgent다.
입력 growth_reports(누적 코딩테스트 강점/약점/변화/개선사항)를 학습 니즈 프로필로 정규화한다.
사용자 선호 직무/언어 등 추가 프로필은 별도로 주어지므로, 여기서는 growth_reports 텍스트에 등장하는 정보만 사용한다. growth_reports는 단일 텍스트이며, 강점/약점/변화/개선 키워드가 문장 속에 섞여 있을 수 있으나 JSON이 아니다.

반드시 아래 JSON만 반환:
{
    "needs_profile": {
      "goal": "당장 개선이 필요한 영역(약점/개선사항 기반)",
      "current_level": "전체 수준 또는 최근 등급/점수",
      "focus_topics": ["반복적으로 약한 알고리즘/도메인 최대 3개"],
      "review_topics": ["최근 악화/잊은 영역 1~2개"],
      "strengths": ["유지/활용할 강점 1~2개"]
    }
  }

추출 가이드:
- growth_reports에 있는 내용으로만 구성한다.
- goal: improvements/weaknesses에서 가장 긴급한 것 1문장.
- focus_topics: 반복된 약점 알고리즘/도메인 키워드 위주 최대 3개.
- review_topics: 최근 악화/퇴보/미완료 영역이 있으면 1~2개.
- preferences/avoid/language/time_budget은 추출하지 않는다(외부 프로필 입력으로 대체 예정).

규칙:
- 새 정보 발명 금지. 근거 없으면 null/빈 문자열/빈 배열.
- JSON 외 텍스트 출력 금지.
"""


SLOT_PLANNER_PROMPT = """
너는 TopicSlotPlannerAgent다.
needs_profile을 참고해 7일치 슬롯을 만든다.

반드시 7개 슬롯을 day 1~7 순서로 생성하며 JSON만 반환:
{
  "slots": [
    {
      "day": 1,
      "topic": "정확한 학습 주제",
      "category": "base|practice|review 중 하나",
      "difficulty": 1,
      "reason": "선택 이유(30자 이내)"
    }
  ]
}

규칙:
- day는 1부터 7까지 1씩 증가.
- topic 중복 금지, category 비율은 base 3 / practice 3 / review 1.
- difficulty는 1~5, needs_profile.current_level을 기준으로 day 1을 설정하고 점진 상승(이전 대비 +0~1, 최대 5). 정보 부족 시 day 1을 1로 시작.
- needs_profile.preferences/avoid 반영.
"""


VIDEO_SELECTOR_PROMPT = """
너는 VideoSelectorAgent다.
입력 슬롯(slots)과 needs_profile을 받아 슬롯별 영상 후보를 선정한다.

절차:
- 각 슬롯마다 video_search_tool을 호출해 query를 날리고 후보 3~5개를 고른다.
- query는 topic+category+difficulty+target_language를 포함한다. 슬롯 difficulty가 없으면 day 순서에 맞춰 1~3 범위로 보수적으로 설정한다.
- 각 후보에 fit_reason(왜 맞는지)과 risks(길이/언어 불일치 등)을 포함한다.

출력(JSON만):
{
  "candidates": [
    {
      "day": 1,
      "topic": "...",
      "videos": [
        {
          "id": "video_id",
          "title": "...",
          "url": "...",
          "video_language": "ko",
          "duration_min": 25,
          "fit_reason": "30자",
          "risks": "20자"
        }
      ]
    }
  ]
}
"""


PLAN_BUILDER_PROMPT = """
너는 PlanBuilderAgent다.
slots와 candidates를 받아 최종 7일 플랜(final_plan)을 만든다.

출력(JSON만):
{
  "final_plan": [
    {
      "day": 1,
      "topic": "...",
      "difficulty": 1,
      "video_title": "...",
      "video_url": "...",
      "video_language": "ko",
      "learning_goals": ["2~3개"],
      "success_criteria": ["2개"],
      "time_plan": "총 40분 (시청 25 + 노트 10 + 복습 5)",
      "why_selected": "30자",
      "warmup": "5분 개념 훑기",
      "review": "5분 전일 복습"
    }
  ]
}

규칙:
- day 1~7 순서 맞추기, video_url 중복 금지.
- difficulty는 슬롯 값을 기본으로 하되 누락 시 day 1=1에서 +0~1씩 증가(최대 5).
- learning_goals는 슬롯 topic과 직결.
- success_criteria는 체크 가능 표현 사용.
- 필요 시 candidates 없으면 topic 기준으로 placeholder를 작성하되 url은 빈 문자열 금지(검색 링크라도 넣기).
"""


MAIN_PROMPT = """
너는 WeeklyStudyPlannerDeepAgent다.
입력: user_id, target_language, growth_reports
출력: final_plan(7개), slots, needs_profile

호출 순서:
1) report-analyzer task → needs_profile 생성
2) slot-planner task → slots 생성
3) video-selector task → candidates 생성
4) plan-builder task → final_plan 생성
5) validate_plan_tool → 검증

실패 대응:
- 검증 실패 시 slots를 한 번 조정하거나 video-selector 재호출 후 plan-builder 재호출.
- 여전히 실패면 plan-builder를 간소화 모드(성공기준 1개, time_plan 요약)로 다시 실행 후 validate.

반환은 반드시 JSON:
{
  "needs_profile": {...},
  "slots": [...],
  "candidates": [...],
  "final_plan": [...],
  "validation": {"ok": bool, "issues": [...]}
}

규칙:
- 새로운 정보 발명 금지, growth_reports/slots/candidates 내 데이터만 사용.
- video_search_tool은 하루 최대 2회 호출.
- description 필드에는 입력 요약 2~3줄만 넣어 토큰을 절약한다.
"""


def create_weekly_study_planner_agent(model_name: str = DEFAULT_MODEL_NAME):
    """7일 학습 추천 deep-agent를 생성한다."""
    base_model = ChatOpenAI(model=model_name, temperature=0)

    return create_deep_agent(
        model=base_model,
        tools=[validate_plan_tool, video_search_tool],
        subagents=[
            {
                "name": "report-analyzer",
                "description": "growth_reports를 needs_profile로 정규화",
                "system_prompt": REPORT_ANALYZER_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "slot-planner",
                "description": "7일 슬롯(topic/category/difficulty) 설계",
                "system_prompt": SLOT_PLANNER_PROMPT,
                "tools": [],
                "model": base_model,
            },
            {
                "name": "video-selector",
                "description": "슬롯에 맞는 영상 후보 검색 및 점수화",
                "system_prompt": VIDEO_SELECTOR_PROMPT,
                "tools": [video_search_tool],
                "model": base_model,
            },
            {
                "name": "plan-builder",
                "description": "7일 최종 플랜 생성",
                "system_prompt": PLAN_BUILDER_PROMPT,
                "tools": [],
                "model": base_model,
            },
        ],
        system_prompt=MAIN_PROMPT,
    )


__all__ = [
    "create_weekly_study_planner_agent",
    "validate_plan_tool",
    "video_search_tool",
]
