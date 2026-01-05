from typing import Any, Dict, List
from langchain_core.tools import tool
from dotenv import load_dotenv
load_dotenv()


def _ensure_django_ready():
    """apps.ready가 False면 django.setup()을 시도한다."""
    try:
        import django
        from django.apps import apps
    except Exception:
        return False
    if apps.ready:
        return True
    try:
        django.setup()
        return True
    except Exception:
        return False


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

    if not _ensure_django_ready():
        return {"query": query, "results": [], "note": "Django 설정/모델이 준비되지 않았습니다(DJANGO_SETTINGS_MODULE 확인 필요)."}

    try:
        model = apps.get_model(app_label="planner", model_name="RecommendedVideo")
    except Exception as exc:
        return {"query": query, "results": [], "note": f"RecommendedVideo 모델 조회 실패: {exc}"}
    if not model:
        return {"query": query, "results": [], "note": "planner.RecommendedVideo 모델을 찾을 수 없습니다"}

    try:
        qs = model.objects.all()
        if query:
            qs = qs.filter(Q(summary__icontains=query) | Q(category__icontains=query) | Q(domain__icontains=query))
        qs = qs.order_by("-created_at")[:5]  # 후보 수 축소

        results = [
            {
                "id": obj.id,
                "video_url": getattr(obj, "video_url", None),
                "summary": (getattr(obj, "summary", None) or "")[:300],  # 요약 길이 제한
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
