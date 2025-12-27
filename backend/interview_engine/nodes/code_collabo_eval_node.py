from __future__ import annotations

import re
from typing import Any, Dict, List

from django.core.cache import cache

from interview_engine.utils.checkpoint_reader import load_chapter_channel_values


def _clamp01(x: float) -> float:
    try:
        x = float(x)
    except Exception:
        return 0.0
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x)


_PREFIX_PATTERN = re.compile(r"^\s*\[([A-Z]+)")


def _coerce_list(raw: Any) -> List[str]:
    """list/str만 받아서 문자열 리스트로 통일."""
    if not raw:
        return []
    if isinstance(raw, list):
        out: List[str] = []
        for it in raw:
            if it is None:
                continue
            s = str(it).strip()
            if s:
                out.append(s)
        return out
    if isinstance(raw, str):
        return [raw.strip()] if raw.strip() else []
    return []


def _extract_prefix(line: str) -> str:
    m = _PREFIX_PATTERN.match(str(line or ""))
    return m.group(1) if m else ""


def _pull_feedback(container: Any, key: str) -> List[str]:
    """container와 container.get('meta') 둘 다에서 찾는다."""
    if not isinstance(container, dict):
        return []
    direct = _coerce_list(container.get(key))
    if direct:
        return direct
    meta_part = container.get("meta")
    if isinstance(meta_part, dict):
        return _coerce_list(meta_part.get(key))
    return []


def _count_prefixes(lines: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for line in lines:
        p = _extract_prefix(line)
        if not p:
            continue
        counts[p] = counts.get(p, 0) + 1
    return counts


def _has_entrypoint_solution(code: str) -> bool:
    return bool(re.search(r"^\s*def\s+solution\s*\(", code or "", flags=re.M))


def _has_placeholder(code: str) -> bool:
    if not code:
        return True
    if re.search(r"^\s*pass\s*$", code, flags=re.M):
        return True
    if re.search(r"TODO|FIXME", code, flags=re.I):
        return True
    if re.search(r"NotImplementedError", code):
        return True
    if re.search(r"^\s*\.\.\.\s*$", code, flags=re.M):
        return True
    return False


def _count_function_lengths(code: str) -> Dict[str, Any]:
    lines = (code or "").splitlines()
    idxs: List[int] = []
    for i, ln in enumerate(lines):
        if re.match(r"^\s*def\s+[A-Za-z_][A-Za-z0-9_]*\s*\(", ln):
            idxs.append(i)
    if not idxs:
        return {"fn_count": 0, "max_fn_lines": 0, "avg_fn_lines": 0.0}

    fn_lens: List[int] = []
    for k, start in enumerate(idxs):
        end = idxs[k + 1] if (k + 1) < len(idxs) else len(lines)
        fn_lens.append(max(1, end - start))

    mx = max(fn_lens) if fn_lens else 0
    avg = (sum(fn_lens) / len(fn_lens)) if fn_lens else 0.0
    return {"fn_count": len(fn_lens), "max_fn_lines": mx, "avg_fn_lines": round(avg, 2)}


def _score_readability_12(prefix_cnt: Dict[str, int]) -> Dict[str, Any]:
    n = prefix_cnt.get("N", 0)
    d = prefix_cnt.get("D", 0)
    i = prefix_cnt.get("I", 0)
    q = prefix_cnt.get("Q", 0)
    era = prefix_cnt.get("ERA", 0)
    e = prefix_cnt.get("E", 0)
    w = prefix_cnt.get("W", 0)
    a = prefix_cnt.get("A", 0)

    readability_issues = (n + d + i + q + era) + 0.25 * (e + w) + 0.5 * a

    P = 12.0
    if readability_issues <= 0:
        score = P
    elif readability_issues <= 2:
        score = 0.85 * P
    elif readability_issues <= 5:
        score = 0.65 * P
    elif readability_issues <= 10:
        score = 0.40 * P
    else:
        score = 0.15 * P

    score = float(round(score, 2))
    return {
        "score": score,
        "issues": round(readability_issues, 2),
        "evidence": {"N": n, "D": d, "I": i, "Q": q, "ERA": era, "E": e, "W": w, "A": a},
        "feedback": [
            f"- 가독성 이슈량: {readability_issues:.2f} → {score:.2f}/12 (N/D/I/Q/ERA + 0.25*(E+W) + 0.5*A)"
        ],
    }


def _score_maintainability_9(prefix_cnt: Dict[str, int], fn_len_ev: Dict[str, Any]) -> Dict[str, Any]:
    c = prefix_cnt.get("C", 0)
    ruf = prefix_cnt.get("RUF", 0)
    b = prefix_cnt.get("B", 0)
    a = prefix_cnt.get("A", 0)
    i = prefix_cnt.get("I", 0)
    tid = prefix_cnt.get("TID", 0)

    max_fn = int(fn_len_ev.get("max_fn_lines") or 0)
    fn_len_pen = 0
    if max_fn >= 80:
        fn_len_pen = 3
    elif max_fn >= 50:
        fn_len_pen = 2
    elif max_fn >= 35:
        fn_len_pen = 1

    maintain_issues = (2.0 * c) + (1.5 * ruf) + (1.2 * b) + (0.6 * a) + (0.4 * i) + (0.2 * tid) + fn_len_pen

    P = 9.0
    if maintain_issues <= 0:
        score = P
    elif maintain_issues <= 2:
        score = 0.85 * P
    elif maintain_issues <= 5:
        score = 0.65 * P
    elif maintain_issues <= 10:
        score = 0.40 * P
    else:
        score = 0.15 * P

    score = float(round(score, 2))
    return {
        "score": score,
        "issues": round(maintain_issues, 2),
        "evidence": {"C": c, "RUF": ruf, "B": b, "A": a, "I": i, "TID": tid, "max_fn_lines": max_fn, "fn_len_pen": fn_len_pen},
        "feedback": [
            f"- 유지보수 이슈량: {maintain_issues:.2f} → {score:.2f}/9 (2*C + 1.5*RUF + 1.2*B + 0.6*A + 0.4*I + 0.2*TID + fn_len_pen)"
        ],
    }


def _score_completeness_9(prefix_cnt: Dict[str, int], code: str) -> Dict[str, Any]:
    f = prefix_cnt.get("F", 0)
    b = prefix_cnt.get("B", 0)
    s = prefix_cnt.get("S", 0)
    ruf = prefix_cnt.get("RUF", 0)

    has_solution = _has_entrypoint_solution(code)
    has_placeholder = _has_placeholder(code)

    comp_issues = (2.5 * f) + (1.3 * b) + (2.0 * s) + (1.0 * ruf)
    if not has_solution:
        comp_issues += 4.0
    if has_placeholder:
        comp_issues += 3.0

    P = 9.0
    if comp_issues <= 0:
        score = P
    elif comp_issues <= 2:
        score = 0.85 * P
    elif comp_issues <= 5:
        score = 0.60 * P
    elif comp_issues <= 9:
        score = 0.35 * P
    else:
        score = 0.10 * P

    score = float(round(score, 2))
    return {
        "score": score,
        "issues": round(comp_issues, 2),
        "evidence": {"F": f, "B": b, "S": s, "RUF": ruf, "has_solution": has_solution, "placeholder": has_placeholder},
        "feedback": [
            f"- 완성도 이슈량: {comp_issues:.2f} → {score:.2f}/9 (2.5*F + 1.3*B + 2.0*S + 1.0*RUF + solution/placeholder 보정)"
        ],
    }


def _pick_top_feedback(lines: List[str], limit: int = 12) -> List[str]:
    out: List[str] = []
    seen = set()
    for line in lines:
        s = (line or "").strip()
        if not s:
            continue
        if s in seen:
            continue
        seen.add(s)
        out.append(s)
        if len(out) >= limit:
            break
    return out


def code_collabo_eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    code_quality_feedback / collaboration_feedback 기반 rule-based 평가
    - 가독성(12점): N/D/I/Q/ERA + 0.25*(E+W) + 0.5*A
    - 유지보수성(9점): 2*C + 1.5*RUF + 1.2*B + 0.6*A + 0.4*I + 0.2*TID + 함수길이 패널티
    - 완성도(9점): 2.5*F + 1.3*B + 2.0*S + 1.0*RUF + (solution 없으면 +4) + (placeholder 있으면 +3)
    - 보너스(5점): 치명 이슈(F/S)·큰 C 유무 기준으로 균형 점수 부여
    - 총점 35점, score01 = 총점/35 클램프
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
        state["code_collab_evidence"] = {}
        return state

    # ---- Redis/Checkpoint 조회
    meta_key = f"livecoding:{session_id}:meta"
    cache_meta = cache.get(meta_key) or {}
    chap2 = load_chapter_channel_values(session_id, "chapter2")
    chap2_hint = load_chapter_channel_values(session_id, "chapter2_hint")

    quality_fb: List[str] = []
    collab_fb: List[str] = []
    quality_source: List[str] = []
    collab_source: List[str] = []

    # 1) state
    quality_fb = _coerce_list(state.get("code_quality_feedback"))
    if quality_fb:
        quality_source.append("state")
    collab_fb = _coerce_list(state.get("collaboration_feedback"))
    if collab_fb:
        collab_source.append("state")

    # 2) cache meta
    if not quality_fb:
        quality_fb = _pull_feedback(cache_meta, "code_quality_feedback")
        if quality_fb:
            quality_source.append("cache_meta")
    if not collab_fb:
        collab_fb = _pull_feedback(cache_meta, "collaboration_feedback")
        if collab_fb:
            collab_source.append("cache_meta")

    # 3) checkpoints
    if not quality_fb:
        quality_fb = _pull_feedback(chap2, "code_quality_feedback")
        if quality_fb:
            quality_source.append("checkpoint_chapter2")
    if not collab_fb:
        collab_fb = _pull_feedback(chap2, "collaboration_feedback")
        if collab_fb:
            collab_source.append("checkpoint_chapter2")

    if not quality_fb:
        quality_fb = _pull_feedback(chap2_hint, "code_quality_feedback")
        if quality_fb:
            quality_source.append("checkpoint_chapter2_hint")
    if not collab_fb:
        collab_fb = _pull_feedback(chap2_hint, "collaboration_feedback")
        if collab_fb:
            collab_source.append("checkpoint_chapter2_hint")

    # ---- 코드 스냅샷 (완성도 보조 신호: solution/placeholder/함수길이)
    code_key = f"livecoding:{session_id}:code"
    code_data = cache.get(code_key) or {}
    latest = (code_data.get("latest") or {})
    cache_code = _safe_str(latest.get("code") or "").strip()
    ckpt_code = _safe_str(chap2.get("code") or "").strip()
    code = cache_code or ckpt_code

    # ---- prefix 카운트 (품질/협업 피드백을 모두 합산)
    prefix_counts = _count_prefixes(quality_fb + collab_fb)

    # ---- 스코어 계산
    read_stats = _score_readability_12(prefix_counts)
    fn_len_ev = _count_function_lengths(code)
    maint_stats = _score_maintainability_9(prefix_counts, fn_len_ev)
    comp_stats = _score_completeness_9(prefix_counts, code)

    # 보너스(5점): 치명 F/S 없고 C 적으면 높게
    fatal = prefix_counts.get("F", 0) + prefix_counts.get("S", 0)
    big_c = prefix_counts.get("C", 0)
    if fatal == 0 and big_c == 0:
        bonus = 5.0
    elif fatal == 0 and big_c <= 1:
        bonus = 4.0
    elif fatal <= 1 and big_c <= 2:
        bonus = 3.0
    else:
        bonus = 1.0

    total_35 = float(round(read_stats["score"] + maint_stats["score"] + comp_stats["score"] + bonus, 2))
    score01 = _clamp01(total_35 / 35.0)

    # ---- 피드백 메시지
    fb_lines: List[str] = []
    fb_lines.append("### 코드 협업 평가 (rule-based, 35점 만점)")
    fb_lines.append(f"- 총점: **{total_35:.2f}/35** (score01={score01:.2f})")
    fb_lines.append(f"- 구성: 가독성 {read_stats['score']:.2f}/12, 유지보수성 {maint_stats['score']:.2f}/9, 완성도 {comp_stats['score']:.2f}/9, 보너스 {bonus:.2f}/5")
    fb_lines.append("")
    fb_lines.append(f"#### 1) 가독성 (readability issues={read_stats['issues']:.2f})")
    fb_lines.extend(read_stats["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 2) 유지보수성 (maintainability issues={maint_stats['issues']:.2f})")
    fb_lines.extend(maint_stats["feedback"])
    fb_lines.append(f"- 함수 길이: fn_count={fn_len_ev.get('fn_count')}, max_fn_lines={fn_len_ev.get('max_fn_lines')}, avg_fn_lines={fn_len_ev.get('avg_fn_lines')}")
    fb_lines.append("")
    fb_lines.append(f"#### 3) 완성도 (completeness issues={comp_stats['issues']:.2f})")
    fb_lines.extend(comp_stats["feedback"])
    fb_lines.append("")
    fb_lines.append("#### 4) 보너스(정적 품질 균형, 5점)")
    fb_lines.append(f"- fatal(F+S)={fatal}, C={big_c} → bonus={bonus:.2f}")
    fb_lines.append("")
    fb_lines.append("### 코드 품질 피드백 원본")
    fb_lines.extend(_pick_top_feedback(quality_fb, limit=50) or ["- (없음)"])
    fb_lines.append("")
    fb_lines.append("### 협업/커뮤니케이션 피드백 원본")
    fb_lines.extend(_pick_top_feedback(collab_fb, limit=50) or ["- (없음)"])

    state["code_collab_score"] = round(score01, 4)
    state["code_collab_score_35"] = total_35
    state["code_collab_feedback"] = "\n".join(fb_lines).strip()
    state["code_collab_evidence"] = {
        "prefix_counts": prefix_counts,
        "readability": read_stats["evidence"],
        "maintainability": maint_stats["evidence"],
        "completeness": comp_stats["evidence"],
        "bonus": bonus,
        "quality_source": quality_source,
        "collaboration_source": collab_source,
        "quality_feedback_count": len(quality_fb),
        "collaboration_feedback_count": len(collab_fb),
    }

    state["status"] = "done"
    return state
