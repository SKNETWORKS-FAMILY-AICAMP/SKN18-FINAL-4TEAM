# backend/interview_engine/nodes/code_collabo_eval_node.py

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


def _count_lines(code: str) -> int:
    if not code:
        return 0
    return len(code.splitlines())


def _basic_style_checks(code: str) -> Tuple[float, List[str]]:
    """
    Ruff 같은 정적 분석이 없더라도 '최소한'의 품질 신호를 뽑는 휴리스틱.
    반환: (score01, feedback_lines)
    """
    if not code.strip():
        return 0.0, ["- 코드가 비어 있습니다."]

    lines = code.splitlines()
    long_lines = [ln for ln in lines if len(ln) > 120]
    has_docstring = bool(re.search(r'^\s*"""', code, re.M))
    has_type_hints = bool(re.search(r"def\s+\w+\(.*\)\s*->\s*\w+", code))
    has_todo = "TODO" in code or "FIXME" in code
    print_count = len(re.findall(r"\bprint\(", code))

    score = 0.5  # 기본
    fb: List[str] = []

    if long_lines:
        score -= min(0.15, 0.02 * len(long_lines))
        fb.append(f"- 120자 초과 라인이 {len(long_lines)}개 있습니다. (가독성 저하)")

    if not has_docstring:
        score -= 0.05
        fb.append("- 함수/모듈 docstring이 없어 의도를 파악하기 어렵습니다.")

    if has_type_hints:
        score += 0.05
        fb.append("- 타입 힌트가 일부 사용되어 가독성과 협업성이 좋습니다.")

    if has_todo:
        score -= 0.03
        fb.append("- TODO/FIXME가 남아 있어 제출 전 정리가 필요합니다.")

    if print_count > 0:
        score -= min(0.10, 0.02 * print_count)
        fb.append(f"- 디버그 print가 {print_count}개 포함되어 있습니다. (제출 전 제거 권장)")

    # 너무 짧으면(거의 미작성) 감점
    if _count_lines(code) < 5:
        score -= 0.25
        fb.append("- 코드가 매우 짧아(미완성 가능성) 구조/품질을 평가하기 어렵습니다.")

    return _clamp01(score), fb


def _collab_signal_from_meta(meta: Dict[str, Any]) -> Tuple[float, List[str]]:
    """
    협업/커뮤니케이션 신호: 메타에서 힌트/질문 횟수 등을 기반으로 간단 점수화.
    - question_cnt: 이미 메타에 저장하고 있지? (CodingQuestionView에서 증가)
    - hint_count: 힌트뷰에서 추정 가능
    """
    question_cnt = int(meta.get("question_cnt") or 0)
    hint_count = int(meta.get("hint_count") or 0)
    tab_switch = int(meta.get("tab_switch_count") or 0)  # 있으면 반영
    copy_paste = int(meta.get("copy_paste_count") or 0)  # 있으면 반영

    # 기본 0.5에서 시작
    score = 0.5
    fb: List[str] = []

    # 질문은 “커뮤니케이션” 관점에서 플러스(너무 많으면 마이너스)
    if question_cnt == 0:
        fb.append("- 면접관 질문 응답/소통 로그가 적습니다. (질문/설명 부족 가능)")
        score -= 0.05
    elif 1 <= question_cnt <= 2:
        fb.append("- 적절한 빈도로 질문/응답이 이루어졌습니다.")
        score += 0.05
    else:
        fb.append("- 질문/응답이 많았습니다. (불확실성/의존성 증가 가능)")
        score -= 0.05

    # 힌트는 의존성으로 감점(너무 과하면 더 감점)
    if hint_count >= 1:
        score -= min(0.25, 0.08 * hint_count)
        fb.append(f"- 힌트를 {hint_count}회 사용했습니다. (자기주도 문제해결 관점에서 감점)")

    # (선택) 부정행위 신호가 메타에 있으면 협업점수에 영향
    if tab_switch >= 3:
        score -= 0.08
        fb.append(f"- 탭 전환이 많았습니다({tab_switch}회). (집중도/환경 이슈 가능)")
    if copy_paste >= 2:
        score -= 0.10
        fb.append(f"- 복붙이 감지되었습니다({copy_paste}회). (출처/자기작성 여부 확인 필요)")

    return _clamp01(score), fb


def code_collabo_eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    step3 - 코드 품질/협업 평가 노드
    입력: state.meta.session_id 기반으로 cache에서 코드/메타 조회
    출력:
      - step/status 업데이트
      - code_collab_score, code_collab_feedback 채움
    """
    state["step"] = "code_collab_eval"
    state["status"] = "running"
    state["error"] = None

    meta = state.get("meta") or {}
    session_id = _safe_str(meta.get("session_id"))

    if not session_id:
        state["status"] = "error"
        state["step"] = "error"
        state["error"] = "meta.session_id가 없습니다."
        state["code_collab_score"] = 0.0
        state["code_collab_feedback"] = "- session_id 누락"
        return state

    meta_key = f"livecoding:{session_id}:meta"
    code_key = f"livecoding:{session_id}:code"

    cached_meta = cache.get(meta_key) or {}
    code_data = cache.get(code_key) or {}
    latest = (code_data.get("latest") or {})
    code = _safe_str(latest.get("code") or "")

    # 1) 코드 스타일/품질 휴리스틱
    style_score, style_fb = _basic_style_checks(code)

    # 2) 협업/커뮤니케이션 휴리스틱
    collab_score, collab_fb = _collab_signal_from_meta(cached_meta)

    # 3) 합산 (원하면 가중치 바꿔)
    score = _clamp01(0.65 * style_score + 0.35 * collab_score)

    feedback_lines: List[str] = []
    feedback_lines.append("### 품질 신호")
    feedback_lines.extend(style_fb or ["- (피드백 없음)"])
    feedback_lines.append("")
    feedback_lines.append("### 협업/커뮤니케이션 신호")
    feedback_lines.extend(collab_fb or ["- (피드백 없음)"])

    state["code_collab_score"] = round(score, 4)
    state["code_collab_feedback"] = "\n".join(feedback_lines).strip()

    # 다음 노드로
    state["status"] = "running"
    return state
