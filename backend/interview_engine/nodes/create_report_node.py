# backend/interview_engine/nodes/create_report_node.py
from __future__ import annotations

from typing import Any, Dict, List, Tuple


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


def _grade_from_score(score01: float) -> str:
    s = _clamp01(score01)
    if s >= 0.90:
        return "A"
    if s >= 0.80:
        return "B"
    if s >= 0.70:
        return "C"
    if s >= 0.60:
        return "D"
    if s >= 0.50:
        return "E"
    return "F"


def _render_markdown(
    final_score: float,
    final_grade: str,
    code_score: float,
    code_feedback: str,
    problem_score: float,
    problem_feedback: str,
    flags: List[str],
) -> str:
    flags_md = "\n".join([f"- {f}" for f in (flags or [])]) or "- (없음)"

    md = f"""# 코딩 테스트 결과 리포트

## 요약
- 최종 점수: **{final_score:.2f}**
- 최종 등급: **{final_grade}**
- 플래그:
{flags_md}

---

## 코드 품질/협업 평가
점수: **{code_score:.2f}**

{code_feedback.strip() if code_feedback else "- (피드백 없음)"}

---

## 문제 해결 평가
점수: **{problem_score:.2f}**

{problem_feedback.strip() if problem_feedback else "- (피드백 없음)"}

---

> 본 리포트는 자동 생성된 결과이며, 실제 면접 판단을 보조하기 위한 참고 자료입니다.
"""
    return md


def create_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    - code_collab_eval_node / problem_solving_eval_node에서 만든 결과를 합산
    - final_score/final_grade/final_report_markdown/final_flags 채움
    - step/status를 saved/done으로 확정
    """

    # 이전 노드 결과(없으면 0)
    code_score = _clamp01(state.get("code_collab_score") or 0.0)
    problem_score = _clamp01(state.get("problem_score") or 0.0)

    code_feedback = state.get("code_collab_feedback") or ""
    problem_feedback = state.get("problem_feedback") or ""

    # 가중치(원하면 여기만 바꾸면 됨)
    w_code = float(state.get("weight_code") or 0.4)
    w_prob = float(state.get("weight_problem") or 0.6)
    w_sum = (w_code + w_prob) if (w_code + w_prob) > 0 else 1.0

    final_score = _clamp01((w_code * code_score + w_prob * problem_score) / w_sum)
    final_grade = _grade_from_score(final_score)

    flags: List[str] = list(state.get("final_flags") or [])
    # 점수 기반 자동 플래그 예시(원하면 제거/수정)
    if final_score < 0.3 and "low_score" not in flags:
        flags.append("low_score")
    if code_score < 0.2 and "code_quality_risk" not in flags:
        flags.append("code_quality_risk")
    if problem_score < 0.2 and "problem_solving_risk" not in flags:
        flags.append("problem_solving_risk")

    md = _render_markdown(
        final_score=final_score,
        final_grade=final_grade,
        code_score=code_score,
        code_feedback=code_feedback,
        problem_score=problem_score,
        problem_feedback=problem_feedback,
        flags=flags,
    )

    # 최종 결과 저장
    state["final_score"] = round(final_score, 4)
    state["final_grade"] = final_grade
    state["final_report_markdown"] = md
    state["final_flags"] = flags

    # UI 매핑용 step/status
    state["step"] = "saved"
    state["status"] = "done"
    state["error"] = None

    # showreport.vue에서 "LangGraph 최종 Output" 펼쳐보기용
    # (원하면 key명을 showreport.vue에 맞춰 바꾸면 됨)
    state["graph_output"] = dict(state)

    return state
