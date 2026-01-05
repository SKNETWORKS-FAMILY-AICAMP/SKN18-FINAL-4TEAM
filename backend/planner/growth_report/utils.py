import json
from django.db import transaction
from django.db.models import Max
from django.utils.timezone import now
from api.models import UserGrowthInsight
from django.db.utils import ProgrammingError
from typing import Any, Dict, List
from langchain_core.messages import SystemMessage, HumanMessage
from interview_engine.llm import get_llm
from .state import ReportState

def _call_llm(system_prompt: str, user_prompt: str) -> str:
    model = get_llm("report")
    resp = model.invoke([SystemMessage(content=system_prompt), HumanMessage(content=user_prompt)])
    return getattr(resp, "content", None) or str(resp)


def _parse_json(content: str) -> Dict[str, Any]:
    try:
        return json.loads(content)
    except Exception:
        return {}


def _reports_to_text(state: ReportState) -> str:
    reps = state.get("reports") or []
    if not reps:
        return "(보고서 없음)"
    texts: List[str] = []
    for idx, r in enumerate(reps, 1):
        header = f"[리포트 {idx}]"
        # 비어 있지 않은 섹션만 붙여서 불필요한 빈 줄 제거
        raw_sections = [
            r.get("report_md"),
            r.get("code_feedback"),
            r.get("consistency_feedback"),
            r.get("improvement"),
            r.get("comprehensive_evaluation"),
        ]
        sections: List[str] = []
        for sec in raw_sections:
            if sec is None:
                continue
            if isinstance(sec, (list, dict)):
                try:
                    sec = json.dumps(sec, ensure_ascii=False)
                except Exception:
                    sec = str(sec)
            else:
                sec = str(sec)
            sec = sec.strip()
            if sec:
                sections.append(sec)
        body = "\n\n".join(sections)
        texts.append(f"{header}\n\n{body}")
    return "\n\n".join(texts)


def _normalize_algorithms(raw: Any) -> List[str]:
    """problem_algorithm 정규화: list/JSON 문자열/기타 → 문자열 리스트"""
    if raw is None:
        return []
    if isinstance(raw, list):
        out: List[str] = []
        for it in raw:
            if it is None:
                continue
            if isinstance(it, (list, dict)):
                try:
                    out.append(json.dumps(it, ensure_ascii=False))
                except Exception:
                    out.append(str(it))
            else:
                txt = str(it).strip()
                if txt:
                    out.append(txt)
        return out
    if isinstance(raw, str):
        txt = raw.strip()
        if not txt:
            return []
        try:
            return _normalize_algorithms(json.loads(txt))
        except Exception:
            return [txt]
    return [str(raw).strip()]


def collect_low_score_algorithms(
    reports: List[Dict[str, Any]],
    threshold: float = 70.0,
) -> List[Dict[str, Any]]:
    """
    final_score가 threshold 미만인 리포트에서 등장한 알고리즘 태그 목록.
    - 중복 제거 후 count까지 포함해 반환.
    반환 예: [{"algorithm": "BFS", "count": 2}, ...]
    """
    buckets: Dict[str, int] = {}

    for r in reports or []:
        try:
            score = float(r.get("final_score"))
        except Exception:
            continue
        if score >= threshold:
            continue
        for algo in _normalize_algorithms(r.get("problem_algorithm")):
            if not algo:
                continue
            buckets[algo] = buckets.get(algo, 0) + 1

    results = [{"algorithm": k, "count": v} for k, v in buckets.items()]
    results.sort(key=lambda x: (-x["count"], x["algorithm"]))
    return results


def collect_high_score_algorithms(
    reports: List[Dict[str, Any]],
    threshold: float = 90.0,
) -> List[Dict[str, Any]]:
    """
    final_score가 threshold 이상인 리포트에서 등장한 알고리즘 태그 목록.
    - 중복 제거 후 count 포함
    반환 예: [{"algorithm": "BFS", "count": 3}, ...]
    """
    buckets: Dict[str, int] = {}

    for r in reports or []:
        try:
            score = float(r.get("final_score"))
        except Exception:
            continue
        if score < threshold:
            continue
        for algo in _normalize_algorithms(r.get("problem_algorithm")):
            if not algo:
                continue
            buckets[algo] = buckets.get(algo, 0) + 1

    results = [{"algorithm": k, "count": v} for k, v in buckets.items()]
    results.sort(key=lambda x: (-x["count"], x["algorithm"]))
    return results

def append_growth_state(user_id: str, new_state: dict):
    """
    누적 성장 리포트 append-only 저장
    (user_id 기준 version 증가)
    new_state에는 strengths/weaknesses/improvements/changes/report_ids 포함
    extra_fields로 추가 저장할 필드를 덮어쓸 수 있음.
    """
    report_content = new_state.get("report_content")
    if report_content is None:
        try:
            report_content = json.dumps(new_state, ensure_ascii=False)
        except Exception:
            report_content = str(new_state)

    # report_ids: 리스트 아닌 경우 리스트로 감싸고, 중첩/비문자도 문자열로 정규화
    report_ids_raw = new_state.get("report_ids") or []
    if not isinstance(report_ids_raw, list):
        report_ids_raw = [report_ids_raw]
    report_ids: List[str] = []
    for it in report_ids_raw:
        if isinstance(it, list):
            report_ids.extend(str(x) for x in it)
        else:
            report_ids.append(str(it))

    try:
        with transaction.atomic():
            last_version = (
                UserGrowthInsight.objects
                .select_for_update()
                .filter(user_id=user_id)
                .aggregate(v=Max("version"))
                .get("v")
            )
            next_version = (last_version or 0) + 1

            base = {
                "user_id": user_id,
                "version": next_version,
                "window_size": new_state.get("window_size") or len(report_ids) or 3,
                "report_ids": report_ids,
                "report_content": report_content,
                "created_at": now(),
            }

            obj = UserGrowthInsight.objects.create(
                **base
            )
            return obj
    except ProgrammingError as e:
        # 테이블이 없을 때는 호출자 레벨에서 처리하도록 예외 전달
        print(f"[append_growth_state] table missing: {e}", flush=True)
        raise
