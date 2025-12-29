from __future__ import annotations

import re
from typing import Any, Dict, List

from django.core.cache import cache

from interview_engine.utils.checkpoint_reader import load_chapter_channel_values
from interview_engine.llm import LLM


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
        "evidence": {
            "C": c,
            "RUF": ruf,
            "B": b,
            "A": a,
            "I": i,
            "TID": tid,
            "max_fn_lines": max_fn,
            "fn_len_pen": fn_len_pen,
        },
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
        "evidence": {
            "F": f,
            "B": b,
            "S": s,
            "RUF": ruf,
            "has_solution": has_solution,
            "placeholder": has_placeholder,
        },
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


def _llm_collab_score(
    conversation_log: List[Any],
    question_cnt: Any,
    hint_count: Any,
    code_excerpt: str,
) -> Dict[str, Any]:
    """
    대화/힌트 메타를 LLM으로 평가해 0~10점 협업 점수 반환.
    """
    try:
        q_cnt = int(question_cnt or 0)
    except Exception:
        q_cnt = 0
    try:
        h_cnt = int(hint_count or 0)
    except Exception:
        h_cnt = 0

    conv_text = conversation_log if isinstance(conversation_log, list) else []
    # 코드 일부만 전달 (너무 길지 않게)
    code_excerpt = (code_excerpt or "").strip()
    if len(code_excerpt) > 1200:
        code_excerpt = code_excerpt[:1200] + "\n... (truncated)"

    system_prompt = (
        "당신은 라이브코딩 인터뷰의 협업/커뮤니케이션 평가자입니다. "
        "대화 로그와 질문/힌트 사용 메타를 바탕으로 협업 성숙도를 0~10점으로 채점하고, 짧은 근거를 제시하세요. "
        "출력은 JSON 문자열로 반환합니다."
    )
    human_prompt = (
        f"[메타]\n"
        f"- question_cnt: {q_cnt}\n"
        f"- hint_count: {h_cnt}\n\n"
        f"[대화 로그]\n{conv_text}\n\n"
        f"[코드 발췌]\n{code_excerpt}\n\n"
        "요구사항:\n"
        "1) 협업/소통/힌트 활용/피드백 수용을 종합해 0~10점으로 평가.\n"
        "2) JSON 객체로만 답변: {\"score\": <0~10 number>, \"feedback\": \"짧은 근거\"}\n"
        "3) 점수는 소수 한 자리까지.\n"
    )

    try:
        resp = LLM.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": human_prompt},
            ]
        )
        raw = (getattr(resp, "content", "") or "").strip()
        import json

        data = json.loads(raw)
        score = float(data.get("score", 0.0) or 0.0)
        fb = str(data.get("feedback") or "").strip()
    except Exception:
        score = 0.0
        fb = "LLM 평가 실패로 0점 처리"

    score = max(0.0, min(10.0, score))
    return {"score": score, "feedback": fb}


def code_collabo_eval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    code_quality_feedback / collaboration_feedback 기반 rule-based 평가
    - 품질(35점): 가독성/유지보수성/완성도 + 보너스 (quality prefix 사용)
    - 협업(30점): 의사소통/힌트 품질/피드백 수용 (collaboration prefix 사용, 보너스 없음)
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

    # ---- prefix 카운트 분리
    quality_prefix_counts = _count_prefixes(quality_fb)
    collab_prefix_counts = _count_prefixes(collab_fb)

    # ---- 품질 스코어(35점) - quality prefix 사용
    q_read = _score_readability_12(quality_prefix_counts)
    q_fn_len = _count_function_lengths(code)
    q_maint = _score_maintainability_9(quality_prefix_counts, q_fn_len)
    q_comp = _score_completeness_9(quality_prefix_counts, code)

    fatal_q = quality_prefix_counts.get("F", 0) + quality_prefix_counts.get("S", 0)
    big_c_q = quality_prefix_counts.get("C", 0)
    if fatal_q == 0 and big_c_q == 0:
        bonus_q = 5.0
    elif fatal_q == 0 and big_c_q <= 1:
        bonus_q = 4.0
    elif fatal_q <= 1 and big_c_q <= 2:
        bonus_q = 3.0
    else:
        bonus_q = 1.0

    quality_total_35 = float(round(q_read["score"] + q_maint["score"] + q_comp["score"] + bonus_q, 2))
    quality_score01 = _clamp01(quality_total_35 / 35.0)

    # ---- 협업 스코어(30점) - collaboration prefix 사용 (보너스 없음)
    c_read = _score_readability_12(collab_prefix_counts)  # 의사소통 12
    c_fn_len = _count_function_lengths(code)
    c_maint = _score_maintainability_9(collab_prefix_counts, c_fn_len)  # 힌트 품질 9 (근사)
    c_comp = _score_completeness_9(collab_prefix_counts, code)  # 피드백 수용 9 (근사)

    collab_rule_total_30 = float(round(c_read["score"] + c_maint["score"] + c_comp["score"], 2))
    # rule 기반을 20점 만점으로 스케일
    collab_rule_20 = collab_rule_total_30 * (20.0 / 30.0)

    # LLM 기반 협업 평가(10점 만점)
    llm_result = _llm_collab_score(
        conversation_log=chap2_hint.get("conversation_log") if isinstance(chap2_hint, dict) else [],
        question_cnt=(chap2.get("question_cnt") if isinstance(chap2, dict) else None),
        hint_count=(chap2_hint.get("hint_count") if isinstance(chap2_hint, dict) else None),
        code_excerpt=code,
    )
    collab_llm_10 = llm_result.get("score", 0.0)

    collab_total_30 = float(round(collab_rule_20 + collab_llm_10, 2))
    collab_score01 = _clamp01(collab_total_30 / 30.0)

    # ---- 피드백 메시지
    fb_lines: List[str] = []
    fb_lines.append("### 코드 품질 평가 (rule-based, 35점 만점)")
    fb_lines.append(f"- 총점: **{quality_total_35:.2f}/35** (score01={quality_score01:.2f})")
    fb_lines.append(f"- 구성: 가독성 {q_read['score']:.2f}/12, 유지보수성 {q_maint['score']:.2f}/9, 완성도 {q_comp['score']:.2f}/9, 보너스 {bonus_q:.2f}/5")
    fb_lines.append("")
    fb_lines.append(f"#### 1) 가독성 (readability issues={q_read['issues']:.2f})")
    fb_lines.extend(q_read["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 2) 유지보수성 (maintainability issues={q_maint['issues']:.2f})")
    fb_lines.extend(q_maint["feedback"])
    fb_lines.append(f"- 함수 길이: fn_count={q_fn_len.get('fn_count')}, max_fn_lines={q_fn_len.get('max_fn_lines')}, avg_fn_lines={q_fn_len.get('avg_fn_lines')}")
    fb_lines.append("")
    fb_lines.append(f"#### 3) 완성도 (completeness issues={q_comp['issues']:.2f})")
    fb_lines.extend(q_comp["feedback"])
    fb_lines.append("")
    fb_lines.append("#### 4) 보너스(정적 품질 균형, 5점)")
    fb_lines.append(f"- fatal(F+S)={fatal_q}, C={big_c_q} → bonus={bonus_q:.2f}")
    fb_lines.append("")

    fb_lines.append("### 협업 능력 평가 (rule-based 20점 + LLM 10점 = 30점)")
    fb_lines.append(f"- 총점: **{collab_total_30:.2f}/30** (score01={collab_score01:.2f})")
    fb_lines.append(f"- 구성: rule 기반 20점(의사소통 {c_read['score']:.2f}/12, 힌트 품질 {c_maint['score']:.2f}/9, 피드백 수용 {c_comp['score']:.2f}/9 → 환산 {collab_rule_20:.2f}/20) + LLM {collab_llm_10:.2f}/10")
    fb_lines.append("")
    fb_lines.append(f"#### 1) 의사소통 (readability issues={c_read['issues']:.2f})")
    fb_lines.extend(c_read["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 2) 힌트 품질 (maintainability issues={c_maint['issues']:.2f})")
    fb_lines.extend(c_maint["feedback"])
    fb_lines.append(f"- 함수 길이: fn_count={c_fn_len.get('fn_count')}, max_fn_lines={c_fn_len.get('max_fn_lines')}, avg_fn_lines={c_fn_len.get('avg_fn_lines')}")
    fb_lines.append("")
    fb_lines.append(f"#### 3) 피드백 수용 (completeness issues={c_comp['issues']:.2f})")
    fb_lines.extend(c_comp["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 4) LLM 협업 평가 (10점)")
    fb_lines.append(f"- 점수: {collab_llm_10:.2f}/10")
    fb_lines.append(f"- 근거: {llm_result.get('feedback')}")

    fb_lines.append("### 코드 품질 피드백 원본")
    fb_lines.extend(_pick_top_feedback(quality_fb, limit=50) or ["- (없음)"])
    fb_lines.append("")
    fb_lines.append("### 협업/커뮤니케이션 피드백 원본")
    fb_lines.extend(_pick_top_feedback(collab_fb, limit=50) or ["- (없음)"])

    # collab 점수를 code_collab_score로 사용 (0~1), 원점수도 보관
    state["code_collab_score"] = round(collab_score01, 4)
    state["code_collab_score_30"] = collab_total_30  # 협업 능력 원점수(30점)
    # 품질 35점 결과는 이름에 quality를 명시
    state["code_quality_score_35"] = quality_total_35
    state["code_quality_score01_from_feedback"] = round(quality_score01, 4)
    state["code_collab_feedback"] = "\n".join(fb_lines).strip()
    state["code_collab_evidence"] = {
        "quality_prefix_counts": quality_prefix_counts,
        "collaboration_prefix_counts": collab_prefix_counts,
        "quality_readability": q_read["evidence"],
        "quality_maintainability": q_maint["evidence"],
        "quality_completeness": q_comp["evidence"],
        "quality_bonus": bonus_q,
        "collab_readability": c_read["evidence"],
        "collab_maintainability": c_maint["evidence"],
        "collab_completeness": c_comp["evidence"],
        "collab_llm_score_10": collab_llm_10,
        "collab_rule_20": collab_rule_20,
        "collab_llm_feedback": llm_result.get("feedback"),
        "quality_source": quality_source,
        "collaboration_source": collab_source,
        "quality_feedback_count": len(quality_fb),
        "collaboration_feedback_count": len(collab_fb),
    }

    state["status"] = "done"
    return state