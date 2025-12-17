# backend/interview_engine/nodes/create_report_node.py
from __future__ import annotations

from typing import Any, Dict, List
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


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


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


def _render_markdown(
    final_score: float,
    final_grade: str,
    code_score: float,
    code_feedback: str,
    problem_score: float,
    problem_feedback: str,
    flags: List[str],
    problem_evidence: Dict[str, Any],
    code_collab_evidence: Dict[str, Any],
) -> str:
    flags_md = "\n".join([f"- {f}" for f in (flags or [])]) or "- (없음)"

    problem_text = _safe_str((problem_evidence or {}).get("problem_text") or "")
    submitted_code = _safe_str((problem_evidence or {}).get("submitted_code") or "")

    strategy_answer = _safe_str((problem_evidence or {}).get("strategy_answer") or "")
    last_question_text = _safe_str((code_collab_evidence or {}).get("last_question_text") or "")
    hint_text = _safe_str((code_collab_evidence or {}).get("hint_text") or "")

    return f"""# 코딩 테스트 결과 리포트

## 요약
- 최종 점수: **{final_score:.2f}**
- 최종 등급: **{final_grade}**
- 플래그:
{flags_md}

---

## 원본 문제
{problem_text if problem_text else "(문제 원문을 찾지 못했습니다.)"}

---

## 제출 코드
```python
{submitted_code if submitted_code else "# (제출 코드를 찾지 못했습니다.)"}
"""

def create_report_node(state: Dict[str, Any]) -> Dict[str, Any]:
    print("[create_report_node] ENTER", flush=True)
    try:
        # 호환: node에서 problem_score/feedback 쓰는 경우도 받아줌
        code_score = _clamp01(state.get("code_collab_score") or 0.0)
        code_feedback = _safe_str(state.get("code_collab_feedback") or "")

        problem_score = _clamp01(
            state.get("problem_eval_score")  # FinalEvalState 정식 키
            if state.get("problem_eval_score") is not None
            else state.get("problem_score")  # 과거/호환 키
            or 0.0
        )
        problem_feedback = _safe_str(
            state.get("problem_eval_feedback")
            if state.get("problem_eval_feedback") is not None
            else state.get("problem_feedback")
            or ""
        )

        # evidence (없으면 빈 dict로)
        problem_evidence = dict(state.get("problem_evidence") or {})
        code_collab_evidence = dict(state.get("code_collab_evidence") or {})

        # 가중치
        w_code = float(state.get("weight_code") or 0.4)
        w_prob = float(state.get("weight_problem") or 0.6)
        w_sum = (w_code + w_prob) if (w_code + w_prob) > 0 else 1.0

        final_score = _clamp01((w_code * code_score + w_prob * problem_score) / w_sum)
        final_grade = _grade_from_score(final_score)

        flags: List[str] = list(state.get("final_flags") or [])
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
            problem_evidence=problem_evidence,
            code_collab_evidence=code_collab_evidence,
        )

        # ✅ FinalEvalState 키에 맞춰 저장(중요)
        state["final_score"] = round(final_score, 4)
        state["final_grade"] = final_grade
        state["final_report_markdown"] = md
        state["final_flags"] = flags

        state["problem_eval_score"] = round(problem_score, 4)
        state["problem_eval_feedback"] = problem_feedback

        # 완료 상태
        state["step"] = "saved"
        state["status"] = "done"
        state["error"] = None

        # debug
        state["graph_output"] = dict(state)
        return state

    except Exception as e:
        import traceback
        traceback.print_exc()

        state["step"] = "error"
        state["status"] = "error"
        state["error"] = f"{type(e).__name__}: {e}"
        state["graph_output"] = dict(state)
        return state
