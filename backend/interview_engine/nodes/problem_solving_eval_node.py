# backend/interview_engine/nodes/problem_solving_eval_node.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple
import re

from django.core.cache import cache


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def _is_starter_like(code: str, starter: str) -> bool:
    c = re.sub(r"\s+", "", code or "")
    s = re.sub(r"\s+", "", starter or "")
    if not c or not s:
        return False
    return c == s


def _heuristic_problem_score(code: str, starter_code: str, test_results: Any = None) -> Tuple[float, List[str]]:
    """
    실제 채점(test_results)이 있으면 그걸 우선 반영하고,
    없으면 코드 진행도/구조 기반 휴리스틱으로 점수 생성.
    """
    fb: List[str] = []

    if not code.strip():
        return 0.0, ["- 코드가 비어 있습니다."]

    # 0) test_results가 있으면 최우선 (형태가 뭐든 최대한 해석)
    if test_results is not None:
        try:
            # 예: {"passed": 7, "total": 10} 또는 {"pass_rate": 0.7} 등
            if isinstance(test_results, dict):
                if "pass_rate" in test_results:
                    pr = float(test_results.get("pass_rate") or 0.0)
                    fb.append(f"- 테스트 통과율 기반 점수 반영: pass_rate={pr:.2f}")
                    return _clamp01(pr), fb
                if "passed" in test_results and "total" in test_results:
                    passed = float(test_results.get("passed") or 0.0)
                    total = float(test_results.get("total") or 0.0) or 1.0
                    pr = passed / total
                    fb.append(f"- 테스트 통과율 기반 점수 반영: {int(passed)}/{int(total)}")
                    return _clamp01(pr), fb
        except Exception:
            # 해석 실패하면 휴리스틱으로 폴백
            fb.append("- test_results 해석에 실패해 휴리스틱 점수로 대체했습니다.")

    # 1) 스타터 코드와 동일하면 거의 0점
    if starter_code and _is_starter_like(code, starter_code):
        return 0.05, ["- 제출 코드가 starter_code와 거의 동일합니다. (실질 풀이 진행이 부족)"]

    # 2) 최소 구조 신호
    score = 0.35
    if re.search(r"def\s+solution\s*\(", code):
        score += 0.15
        fb.append("- solution 함수가 정의되어 있습니다.")
    else:
        fb.append("- solution 함수 정의가 확인되지 않습니다. (채점 실패 가능)")

    # 3) 논리 전개 신호
    has_loop = bool(re.search(r"\bfor\b|\bwhile\b", code))
    has_if = bool(re.search(r"\bif\b", code))
    has_return = bool(re.search(r"\breturn\b", code))

    if has_loop:
        score += 0.10
        fb.append("- 반복문 사용이 확인됩니다. (탐색/누적/반복 처리 가능)")
    if has_if:
        score += 0.08
        fb.append("- 조건 분기(if) 사용이 확인됩니다.")
    if has_return:
        score += 0.07
        fb.append("- 반환(return) 로직이 확인됩니다.")

    # 4) 너무 비효율적인 형태(예: 1..n 전부 약수세기 같은 완전탐색) 간단 감점
    brute_pattern = re.search(r"for\s+\w+\s+in\s+range\(\s*1\s*,\s*\w+\s*\+\s*1\s*\)", code)
    nested_for = len(re.findall(r"\bfor\b", code)) >= 2
    if nested_for and brute_pattern:
        score -= 0.12
        fb.append("- 완전탐색/중첩 반복 형태가 보여 시간 복잡도 리스크가 있습니다.")

    # 5) 마무리
    score = _clamp01(score)
    if score >= 0.75:
        fb.append("- 전반적으로 풀이 형태가 갖춰져 있습니다. (정확성/엣지케이스 점검 권장)")
    elif score >= 0.45:
        fb.append("- 기본 골격은 있으나 정확성/최적화/엣지케이스가 부족할 수 있습니다.")
    else:
        fb.append("- 풀이 진행이 제한적입니다. (정답 도출 로직 보강 필요)")

    return score, fb


def problem_solving_eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    step3 - 문제 해결 평가 노드
    - cache에서 meta/code 가져오고
    - (있으면) state.test_results 반영
    - problem_score/problem_feedback 채움
    """
    state["step"] = "problem_eval"
    state["status"] = "running"
    state["error"] = None

    meta = state.get("meta") or {}
    session_id = _safe_str(meta.get("session_id"))

    if not session_id:
        state["status"] = "error"
        state["step"] = "error"
        state["error"] = "meta.session_id가 없습니다."
        state["problem_score"] = 0.0
        state["problem_feedback"] = "- session_id 누락"
        return state

    meta_key = f"livecoding:{session_id}:meta"
    code_key = f"livecoding:{session_id}:code"

    cached_meta = cache.get(meta_key) or {}
    code_data = cache.get(code_key) or {}
    latest = (code_data.get("latest") or {})
    code = _safe_str(latest.get("code") or "")

    starter_code = _safe_str(cached_meta.get("starter_code") or "")
    test_results = state.get("test_results")  # 너네 채점결과를 여기에 넣으면 자동 반영됨

    score, fb = _heuristic_problem_score(code=code, starter_code=starter_code, test_results=test_results)

    state["problem_score"] = round(_clamp01(score), 4)
    state["problem_feedback"] = "\n".join([f"- {x.lstrip('- ').strip()}" for x in (fb or [])]).strip()

    state["status"] = "running"
    return state
