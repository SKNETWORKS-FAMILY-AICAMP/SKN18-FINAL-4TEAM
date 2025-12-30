from __future__ import annotations

import ast
import json
import re
from typing import Any, Dict, List, Tuple

import redis
from django.core.cache import cache
from langgraph.checkpoint.redis import RedisSaver

from interview_engine.llm import get_llm  # noqa: F401  # (필요 시 사용)
from interview_engine.utils.checkpoint_reader import _redis_url, load_chapter_channel_values


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
    """container와 container.get('meta') 둘 다에서 key를 찾는다."""
    if not isinstance(container, dict):
        return []
    direct = _coerce_list(container.get(key))
    if direct:
        return direct
    meta_part = container.get("meta")
    if isinstance(meta_part, dict):
        return _coerce_list(meta_part.get(key))
    return []


def _pull_error(container: Any) -> str:
    if not isinstance(container, dict):
        return ""
    for key in ("ruff_error", "code_quality_error", "collaboration_error"):
        val = container.get(key)
        if val:
            return _safe_str(val)
    meta_part = container.get("meta")
    if isinstance(meta_part, dict):
        for key in ("ruff_error", "code_quality_error", "collaboration_error"):
            val = meta_part.get(key)
            if val:
                return _safe_str(val)
    return ""


def _count_prefixes(lines: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for line in lines:
        p = _extract_prefix(line)
        if not p:
            continue
        counts[p] = counts.get(p, 0) + 1
    return counts


def _has_entrypoint_solution(code: str, function_name: str = "solution") -> bool:
    name = function_name or "solution"
    pattern = rf"^\s*def\s+{re.escape(name)}\s*\("
    return bool(re.search(pattern, code or "", flags=re.M))


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
    if max_fn >= 100:
        fn_len_pen = 3
    elif max_fn >= 75:
        fn_len_pen = 2
    elif max_fn >= 50:
        fn_len_pen = 1

    maintain_issues = (
        (2.0 * c)
        + (1.5 * ruf)
        + (1.2 * b)
        + (0.6 * a)
        + (0.4 * i)
        + (0.2 * tid)
        + fn_len_pen
    )

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
            (
                "- 유지보수 이슈량: "
                f"{maintain_issues:.2f} → {score:.2f}/9 "
                "(2*C + 1.5*RUF + 1.2*B + 0.6*A + 0.4*I + 0.2*TID + fn_len_pen)"
            )
        ],
    }


def _score_completeness_9(
    prefix_cnt: Dict[str, int],
    code: str,
    function_name: str = "solution",
) -> Dict[str, Any]:
    f = prefix_cnt.get("F", 0)
    b = prefix_cnt.get("B", 0)
    s = prefix_cnt.get("S", 0)
    ruf = prefix_cnt.get("RUF", 0)

    has_solution = _has_entrypoint_solution(code, function_name)
    has_placeholder = _has_placeholder(code)

    comp_issues = (2.5 * f) + (1.3 * b) + (2.0 * s) + (1.0 * ruf)
    if not has_solution:
        comp_issues += 4.0
    if has_placeholder:
        comp_issues += 9.0

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
            (
                "- 완성도 이슈량: "
                f"{comp_issues:.2f} → {score:.2f}/9 "
                "(2.5*F + 1.3*B + 2.0*S + 1.0*RUF + solution/placeholder 보정)"
            )
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


# -------- 협업 전용 스코어(communication/hint/feedback) --------
def _score_collab_comm_12(prefix_cnt: Dict[str, int]) -> Dict[str, Any]:
    # N/D/I/Q/ERA만 사용
    n = prefix_cnt.get("N", 0)
    d = prefix_cnt.get("D", 0)
    i = prefix_cnt.get("I", 0)
    q = prefix_cnt.get("Q", 0)
    era = prefix_cnt.get("ERA", 0)

    comm_issues = n + d + i + q + era
    P = 12.0
    if comm_issues <= 0:
        score = P
    elif comm_issues <= 2:
        score = 0.85 * P
    elif comm_issues <= 5:
        score = 0.65 * P
    elif comm_issues <= 10:
        score = 0.40 * P
    else:
        score = 0.15 * P
    score = float(round(score, 2))
    return {
        "score": score,
        "issues": round(comm_issues, 2),
        "evidence": {"N": n, "D": d, "I": i, "Q": q, "ERA": era},
        "feedback": [f"- 의사소통 이슈량: {comm_issues:.2f} → {score:.2f}/12 (N/D/I/Q/ERA)"],
    }


def _score_collab_feedback_9(improvement_ratio: float) -> Dict[str, Any]:
    """
    피드백 수용(9점): 힌트/질문 이후 코드 개선율을 사용.
    improvement_ratio는 0~1 범위 권장.
      - 0.8 이상: 9점
      - 0.5 이상: 7점
      - 0.2 이상: 5점
      - 그 미만: 3점
    """
    try:
        r = float(improvement_ratio)
    except Exception:
        r = 0.0
    if r >= 0.8:
        score = 9.0
    elif r >= 0.5:
        score = 7.0
    elif r >= 0.2:
        score = 5.0
    else:
        score = 3.0
    return {
        "score": float(round(score, 2)),
        "issues": round(1.0 - r, 2),  # 낮을수록 개선 적음
        "evidence": {"improvement_ratio": round(r, 4)},
        "feedback": [f"- 피드백 수용: 개선율={r:.2f} → {score:.2f}/9"],
    }


def _score_collab_hint_count_9(
    hint_count: Any,
    change_ratio: float | None = None,
) -> Dict[str, Any]:
    """
    힌트 품질 9점 = (A*0.6 + B*0.4)*9
      - A(타이밍 60%): hint_count <=3 =>1.0, 초과=>0.6
      - B(빈도 40%): 1회=1.0, 2회=0.8, 3회=0.5, 0회=0.5, 그 이상=0.4
      - change_ratio가 주어지면(0~1) 힌트 요청 전후 코드 변화량을 가중(멀티플라이어 0.5~1.0)
    """
    try:
        hc = int(hint_count if hint_count is not None else 0)
    except Exception:
        hc = 0

    a_factor = 1.0 if hc <= 3 else 0.6
    if hc <= 0:
        b_factor = 0.5
    elif hc == 1:
        b_factor = 1.0
    elif hc == 2:
        b_factor = 0.8
    elif hc == 3:
        b_factor = 0.5
    else:
        b_factor = 0.4

    combined = (a_factor * 0.6) + (b_factor * 0.4)

    # 코드 변화량이 없는데 힌트를 요청한 경우 감점 (0.5~1.0 배)
    if change_ratio is None:
        multiplier = 1.0
    else:
        try:
            cr = float(change_ratio)
        except Exception:
            cr = 0.0
        cr = max(0.0, min(1.0, cr))
        multiplier = 0.5 + 0.5 * cr

    score = float(round(combined * multiplier * 9.0, 2))

    return {
        "score": score,
        "issues": float(hc),
        "evidence": {
            "hint_count": hc,
            "timing_factor": a_factor,
            "freq_factor": b_factor,
            "combined_factor": round(combined, 4),
            "change_ratio": None
            if change_ratio is None
            else round(max(0.0, min(1.0, float(change_ratio))), 4),
            "multiplier": round(multiplier, 3),
        },
        "feedback": [
            (
                "- 힌트 품질: "
                f"hint_count={hc}, timing={a_factor:.2f}, "
                f"freq={b_factor:.2f}, change_mult={multiplier:.2f} → {score:.2f}/9"
            )
        ],
    }


def _load_latest_feedback(session_id: str, chapter: str, field: str) -> Tuple[List[str], str]:
    """
    LangGraph 체크포인트에서 특정 feedback 필드를 로드.
    - thread_id = "{session_id}:{chapter}"
    - checkpoint_ns = "__empty__" 고정
    1) RedisSaver latest → list_checkpoints 역순 스캔
    2) 실패 시 Redis JSON 키 직접 조회 (checkpoint_latest → checkpoint:* 스캔)
    """
    thread_id = f"{session_id}:{chapter}"
    ns = "__empty__"

    # 1) LangGraph RedisSaver
    saver = None
    try:
        saver = RedisSaver.from_conn_string(_redis_url())
    except Exception:
        saver = None

    if saver:
        # 최신 checkpoint 우선
        try:
            tup = saver.get_tuple(thread_id=thread_id, checkpoint_ns=ns)
            if tup and getattr(tup, "checkpoint", None):
                cv = (tup.checkpoint or {}).get("channel_values") or {}
                fb = _coerce_list(cv.get(field))
                if fb:
                    return fb, f"checkpoint_latest:{chapter}"
        except Exception:
            pass

        # 과거 checkpoint 역순 스캔
        try:
            if hasattr(saver, "list_checkpoints"):
                ckpts = saver.list_checkpoints(thread_id=thread_id, checkpoint_ns=ns) or []
                for ck in reversed(ckpts):
                    ckid = getattr(ck, "checkpoint_id", "") or ""
                    try:
                        tup = (
                            saver.get_tuple(
                                thread_id=thread_id,
                                checkpoint_ns=ns,
                                checkpoint_id=ckid,
                            )
                            if ckid
                            else ck
                        )
                    except Exception:
                        tup = ck
                    cv = {}
                    if tup and getattr(tup, "checkpoint", None):
                        cv = (tup.checkpoint or {}).get("channel_values") or {}
                    fb = _coerce_list(cv.get(field))
                    if fb:
                        return fb, f"checkpoint:{chapter}:{ckid or 'scan'}"
        except Exception:
            pass

    # 2) Redis JSON 직접 조회
    try:
        rcli = redis.from_url(_redis_url())
        latest_key = f"checkpoint_latest:{session_id}:{chapter}:{ns}"
        ck_ref = rcli.get(latest_key)
        if ck_ref:
            ck_ref = ck_ref.decode() if isinstance(ck_ref, (bytes, bytearray)) else str(ck_ref)
            try:
                raw = rcli.execute_command("JSON.GET", ck_ref, ".")
                if raw:
                    data = json.loads(raw)
                    cv = (data.get("checkpoint") or {}).get("channel_values") or {}
                    fb = _coerce_list(cv.get(field))
                    if fb:
                        return fb, f"redis_json_latest:{chapter}"
            except Exception:
                pass

        pattern = f"checkpoint:{session_id}:{chapter}:{ns}:*"
        keys = rcli.keys(pattern)
        for k in sorted(keys, reverse=True):
            try:
                raw = rcli.execute_command("JSON.GET", k, ".")
                if not raw:
                    continue
                data = json.loads(raw)
                cv = (data.get("checkpoint") or {}).get("channel_values") or {}
                fb = _coerce_list(cv.get(field))
                if fb:
                    k_str = k.decode() if isinstance(k, (bytes, bytearray)) else str(k)
                    return fb, f"redis_json:{k_str}"
            except Exception:
                continue
    except Exception:
        pass

    return [], "missing"


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
        state["code_collab_feedback"] = "- session_id 누락"
        state["code_collab_evidence"] = {}
        return state

    # ---- Redis/Checkpoint 조회
    meta_key = f"livecoding:{session_id}:meta"
    cache_meta = cache.get(meta_key) or {}
    chap2 = load_chapter_channel_values(session_id, "chapter2")
    chap2_hint = load_chapter_channel_values(session_id, "chapter2_hint")

    # ---- Ruff 오류 확인 (오류면 강한 감점: 0점 처리)
    ruff_error = (
        _pull_error(state)
        or _pull_error(cache_meta)
        or _pull_error(chap2)
        or _pull_error(chap2_hint)
    )
    if ruff_error:
        state["code_collab_score"] = 0.0
        state["code_collab_score_30"] = 0.0
        state["code_quality_score_35"] = 0.0
        state["code_collab_feedback"] = f"### Ruff 실행 실패로 코드 품질/협업 점수를 0점 처리\n- 오류: {ruff_error}"
        state["code_collab_evidence"] = {
            "ruff_error": ruff_error,
            "quality_feedback_count": 0,
            "collaboration_feedback_count": 0,
        }
        state["status"] = "done"
        return state

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

    # 3) checkpoints (단일 챕터 값)
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

    # 4) LangGraph checkpoint 스캔 (chapter2 → chapter2_hint 순서)
    if not quality_fb:
        quality_fb, q_src = _load_latest_feedback(session_id, "chapter2", "code_quality_feedback")
        if quality_fb:
            quality_source.append(q_src)
    if not quality_fb:
        quality_fb, q_src2 = _load_latest_feedback(
            session_id,
            "chapter2_hint",
            "code_quality_feedback",
        )
        if quality_fb:
            quality_source.append(q_src2)

    if not collab_fb:
        collab_fb, c_src = _load_latest_feedback(
            session_id,
            "chapter2",
            "collaboration_feedback",
        )
        if collab_fb:
            collab_source.append(c_src)
    if not collab_fb:
        collab_fb, c_src2 = _load_latest_feedback(
            session_id,
            "chapter2_hint",
            "collaboration_feedback",
        )
        if collab_fb:
            collab_source.append(c_src2)

    # ---- 코드 스냅샷 (완성도 보조 신호: solution/placeholder/함수길이)
    code_key = f"livecoding:{session_id}:code"
    code_data = cache.get(code_key) or {}
    latest = code_data.get("latest") or {}
    cache_code = _safe_str(latest.get("code") or "").strip()
    ckpt_code = _safe_str(chap2.get("code") or "").strip()
    code = cache_code or ckpt_code
    function_name = ""
    problem = cache.get(f"livecoding:{session_id}:problem") or {}
    if isinstance(problem, dict):
        function_name = _safe_str(problem.get("function_name") or "")
    if not function_name:
        function_name = "solution"

    # ---- ruff issues empty + parse fail => hard fail
    if not ruff_error and not quality_fb and not collab_fb and code:
        try:
            ast.parse(code)
        except Exception as exc:
            ruff_error = _safe_str(exc)
            state["code_collab_score"] = 0.0
            state["code_collab_score_30"] = 0.0
            state["code_quality_score_35"] = 0.0
            state["code_collab_feedback"] = (
                "### 코드 파싱 실패로 코드 품질/협업 점수를 0점 처리\n"
                f"- 오류: {ruff_error}"
            )
            state["code_collab_evidence"] = {
                "ruff_error": ruff_error,
                "quality_feedback_count": 0,
                "collaboration_feedback_count": 0,
            }
            state["status"] = "done"
            return state

    # ---- prefix 카운트 분리
    quality_prefix_counts = _count_prefixes(quality_fb)
    collab_prefix_counts = _count_prefixes(collab_fb)

    # ---- 품질 스코어(35점) - quality prefix 사용
    q_read = _score_readability_12(quality_prefix_counts)
    q_fn_len = _count_function_lengths(code)
    q_maint = _score_maintainability_9(quality_prefix_counts, q_fn_len)
    q_comp = _score_completeness_9(quality_prefix_counts, code, function_name)
    has_placeholder = _has_placeholder(code)

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

    quality_total_35 = float(
        round(q_read["score"] + q_maint["score"] + q_comp["score"] + bonus_q, 2),
    )
    if has_placeholder:
        quality_total_35 = 0.0
        bonus_q = 0.0

    # ---- 협업 스코어(30점) - collaboration prefix 전용 스코어 사용 (보너스 없음)
    c_comm = _score_collab_comm_12(collab_prefix_counts)  # 의사소통 12

    # 힌트 품질은 hint_count 기반
    hint_count = chap2_hint.get("hint_count") if isinstance(chap2_hint, dict) else None

    # 코드 변화량(힌트 직후 코드 vs 최신 코드)이 있으면 멀티플라이어로 반영
    hint_code = (
        _safe_str(chap2_hint.get("current_user_code") or "")
        if isinstance(chap2_hint, dict)
        else ""
    )
    latest_code = code  # 이미 최신 스냅샷으로 확보
    change_ratio = None
    if hint_code:
        try:
            change_ratio = 0.0 if hint_code.strip() == latest_code.strip() else 1.0
        except Exception:
            change_ratio = 0.0
    c_hint = _score_collab_hint_count_9(hint_count, change_ratio)

    # 피드백 수용: 힌트 직후 코드 vs 최신 코드의 개선율(길이/함수/placeholder)
    def _code_metrics(txt: str) -> Dict[str, float]:
        lines = (txt or "").splitlines()
        fn_stats = _count_function_lengths(txt)
        has_ph = _has_placeholder(txt)
        return {
            "line_count": len(lines),
            "max_fn_lines": fn_stats.get("max_fn_lines") or 0,
            "fn_count": fn_stats.get("fn_count") or 0,
            "placeholder": 1 if has_ph else 0,
        }

    m_before = _code_metrics(hint_code) if hint_code else _code_metrics(latest_code)
    m_after = _code_metrics(latest_code)

    def _ratio(before: float, after: float, higher_is_better: bool) -> float:
        try:
            b = float(before)
            a = float(after)
        except Exception:
            return 0.0
        if b <= 0 and a <= 0:
            return 1.0
        if b <= 0:
            return 0.0
        diff = (b - a) if higher_is_better else (a - b)
        return max(0.0, min(1.0, diff / max(1.0, abs(b))))

    # 개선율: 라인 수 감소, max 함수 길이 감소, 함수 개수 증가, placeholder 제거 여부
    r_line = _ratio(m_before["line_count"], m_after["line_count"], True)
    r_fnlen = _ratio(m_before["max_fn_lines"], m_after["max_fn_lines"], True)
    r_fncount = _ratio(m_before["fn_count"], m_after["fn_count"], False)
    r_placeholder = (
        1.0
        if (m_before["placeholder"] == 1 and m_after["placeholder"] == 0)
        else 0.0
        if m_before["placeholder"]
        else 1.0
    )

    improvement_ratio = max(
        0.0,
        min(
            1.0,
            (0.25 * r_line)
            + (0.25 * r_fnlen)
            + (0.25 * r_fncount)
            + (0.25 * r_placeholder),
        ),
    )

    c_fb = _score_collab_feedback_9(improvement_ratio)  # 피드백 수용 9

    collab_rule_total_30 = float(
        round(c_comm["score"] + c_hint["score"] + c_fb["score"], 2),
    )
    collab_total_30 = collab_rule_total_30  # 협업은 rule-based 30점만 사용
    if has_placeholder:
        collab_total_30 = 0.0

    # ---- 피드백 메시지
    fb_lines: List[str] = []
    fb_lines.append("### 코드 품질 평가 (rule-based, 35점 만점)")
    if has_placeholder:
        fb_lines.append("- 제출 코드에 placeholder(pass/TODO/...)가 포함되어 0점 처리")
    fb_lines.append(f"- 총점: **{quality_total_35:.2f}/35**")
    fb_lines.append(
        (
            "- 구성: "
            f"가독성 {q_read['score']:.2f}/12, "
            f"유지보수성 {q_maint['score']:.2f}/9, "
            f"완성도 {q_comp['score']:.2f}/9, "
            f"보너스 {bonus_q:.2f}/5"
        ),
    )
    fb_lines.append("")
    fb_lines.append(f"#### 1) 가독성 (readability issues={q_read['issues']:.2f})")
    fb_lines.extend(q_read["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 2) 유지보수성 (maintainability issues={q_maint['issues']:.2f})")
    fb_lines.extend(q_maint["feedback"])
    fb_lines.append(
        (
            "- 함수 길이: "
            f"fn_count={q_fn_len.get('fn_count')}, "
            f"max_fn_lines={q_fn_len.get('max_fn_lines')}, "
            f"avg_fn_lines={q_fn_len.get('avg_fn_lines')}"
        ),
    )
    fb_lines.append("")
    fb_lines.append(f"#### 3) 완성도 (completeness issues={q_comp['issues']:.2f})")
    fb_lines.extend(q_comp["feedback"])
    fb_lines.append("")
    fb_lines.append("#### 4) 보너스(정적 품질 균형, 5점)")
    fb_lines.append(f"- fatal(F+S)={fatal_q}, C={big_c_q} → bonus={bonus_q:.2f}")
    fb_lines.append("")

    fb_lines.append("### 협업 능력 평가 (rule-based 30점)")
    fb_lines.append(f"- 총점: **{collab_total_30:.2f}/30**")
    fb_lines.append(
        (
            "- 구성: "
            f"의사소통 {c_comm['score']:.2f}/12, "
            f"힌트 품질 {c_hint['score']:.2f}/9, "
            f"피드백 수용 {c_fb['score']:.2f}/9 (보너스/LLM 없음)"
        ),
    )
    fb_lines.append("")
    fb_lines.append(f"#### 1) 의사소통 (comm issues={c_comm['issues']:.2f})")
    fb_lines.extend(c_comm["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 2) 힌트 품질 (hint issues={c_hint['issues']:.2f})")
    fb_lines.extend(c_hint["feedback"])
    fb_lines.append("")
    fb_lines.append(f"#### 3) 피드백 수용 (feedback issues={c_fb['issues']:.2f})")
    fb_lines.extend(c_fb["feedback"])
    fb_lines.append("")

    fb_lines.append("### 코드 품질 피드백 원본")
    fb_lines.extend(_pick_top_feedback(quality_fb, limit=50) or ["- (없음)"])
    fb_lines.append("")
    fb_lines.append("### 협업/커뮤니케이션 피드백 원본")
    fb_lines.extend(_pick_top_feedback(collab_fb, limit=50) or ["- (없음)"])

    # ---- state 저장 (정규화 점수 없이 원점수만)
    state["code_collab_score_30"] = collab_total_30
    state["code_quality_score_35"] = quality_total_35
    state["code_collab_feedback"] = "\n".join(fb_lines).strip()
    state["code_collab_evidence"] = {
        "quality_prefix_counts": quality_prefix_counts,
        "collaboration_prefix_counts": collab_prefix_counts,
        "quality_readability": q_read["evidence"],
        "quality_maintainability": q_maint["evidence"],
        "quality_completeness": q_comp["evidence"],
        "quality_bonus": bonus_q,
        "collab_comm": c_comm["evidence"],
        "collab_hint": c_hint["evidence"],
        "collab_feedback": c_fb["evidence"],
        "quality_source": quality_source,
        "collaboration_source": collab_source,
        "quality_feedback_count": len(quality_fb),
        "collaboration_feedback_count": len(collab_fb),
    }

    state["status"] = "done"
    return state
