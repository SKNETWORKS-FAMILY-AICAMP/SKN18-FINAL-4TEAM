from typing import Any, Dict, List, Optional, Union
from langchain_core.tools import tool
from dotenv import load_dotenv
from deepagents import create_deep_agent as build_deep_agent
from langchain_openai import ChatOpenAI
import json
import re
load_dotenv()

DEFAULT_MODEL_NAME = "gpt-5-nano"
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


def _create_agent(*, model_name: str = DEFAULT_MODEL_NAME, tools: Optional[list] = None, system_prompt: Optional[str] = None):
    """deep_agent 인스턴스를 생성하는 래퍼."""
    base_model = ChatOpenAI(model=model_name, temperature=0)
    return build_deep_agent(
        model=base_model,
        tools=tools or [],
        system_prompt=system_prompt,
)
    
def safe_json_parse(text: str) -> Dict[str, Any]:
    """
    LLM 응답에서 JSON을 최대한 안전하게 파싱한다.
    """
    if not text:
        return {}

    # 1) 바로 파싱 시도
    try:
        return json.loads(text)
    except Exception:
        pass

    # 2) ```json ``` 코드블록 제거
    cleaned = re.sub(r"```json|```", "", text).strip()
    try:
        return json.loads(cleaned)
    except Exception:
        pass

    # 3) JSON object 부분만 추출
    match = re.search(r"\{[\s\S]*\}", text)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass

    # 4) 실패 시 로그용 반환
    raise ValueError(f"JSON parsing failed. raw text:\n{text}")


@tool
def video_search_tool(query: Union[str, Dict[str, Any]], limit: int = 5) -> Dict[str, Any]:
    """
    RecommendedVideo 검색 (ArrayField 대응).
    - dict 입력 권장: domain(필수) + category(필수) + code_lang(옵션) AND 필터
    - str 입력: 보조(사용 금지 권장)
    - limit: 반환 개수(기본 5, 최대 20)
    """
    try:
        from django.apps import apps
        from django.db.models import Q
    except Exception as exc:  # pragma: no cover
        return {"query": query, "results": [], "note": f"Django import 실패: {exc}"}

    if not _ensure_django_ready():
        return {"query": query, "results": [], "note": "Django 설정/모델이 준비되지 않았습니다(DJANGO_SETTINGS_MODULE 확인 필요)."}

    try:
        model = apps.get_model(app_label="planner", model_name="RecommendedVideo")
    except Exception as exc:
        return {"query": query, "results": [], "note": f"RecommendedVideo 모델 조회 실패: {exc}"}

    if not model:
        return {"query": query, "results": [], "note": "planner.RecommendedVideo 모델을 찾을 수 없습니다"}

    def _as_list(x: Any) -> List[str]:
        if not x:
            return []
        if isinstance(x, list):
            return [str(v).strip() for v in x if str(v).strip()]
        return [str(x).strip()] if str(x).strip() else []

    debug = {}
    limit = max(1, min(int(limit or 5), 20))
    filters = Q()

    # ✅ dict 입력: domain/category/code_lang 중심
    if isinstance(query, dict):
        domain = (query.get("domain") or "").strip()
        category_vals = _as_list(query.get("category"))
        code_lang_vals = [s.lower() for s in _as_list(query.get("code_lang"))]

        # domain은 반드시 둘 중 하나라고 했으니 equality로 강하게
        if domain in ("algorithm", "live_coding"):
            filters &= Q(domain=domain)
        else:
            # 잘못 들어오면 결과 0이 나오게 하는 대신, note로 알려줌
            return {
                "query": query,
                "results": [],
                "note": f"invalid domain: {domain} (expected 'algorithm'|'live_coding')",
            }

        # category는 ArrayField -> overlap
        if category_vals:
            filters &= Q(category__overlap=category_vals)
        else:
            return {"query": query, "results": [], "note": "missing category (list)"}

        # code_lang도 ArrayField -> overlap (옵션)
        if code_lang_vals:
            filters &= Q(code_lang__overlap=code_lang_vals)

        debug = {
            "mode": "dict",
            "domain": domain,
            "category": category_vals,
            "code_lang": code_lang_vals,
        }

    else:
        # str 입력은 보조: 쓰지 않는 걸 권장
        qstr = (query or "").strip()
        if not qstr:
            return {"query": query, "results": [], "note": "empty query"}
        filters = Q(summary__icontains=qstr) | Q(domain__icontains=qstr)
        debug = {"mode": "str", "raw": qstr}

    try:
        qs = (
            model.objects.all()
            .only("id", "video_url", "summary")
            .filter(filters)
            .order_by("?")[:limit]
        )
        results = [
            {
                "id": obj.id,
                "video_url": getattr(obj, "video_url", None),
                "summary": getattr(obj, "summary", None),
            }
            for obj in qs
        ]
    except Exception as exc:  # pragma: no cover
        return {"query": query, "results": [], "note": f"DB 조회 실패: {exc}", "debug": debug}

    return {"query": query, "results": results, "note": ("ok" if results else "no results"), "debug": debug}
