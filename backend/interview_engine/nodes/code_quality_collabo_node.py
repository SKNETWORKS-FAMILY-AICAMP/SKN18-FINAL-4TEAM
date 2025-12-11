import re
import subprocess
import tempfile
from typing import Any, Dict, List

from interview_engine.state import CodingState

RUFF_CMD = [
    "ruff",
    "check",
    "--quiet",
    "--output-format",
    "concise",
    "--select",
    "F,E,W,B,C,S,UP,A,TID,RUF,N,D,Q,I,ERA",
]


def _run_ruff(source_code: str, language: str) -> List[Dict[str, Any]]:
    """
    Ruff를 한 번 실행해서 진단 리스트를 리턴
    """
    if not source_code.strip():
        return []

    # language별로 확장자만 다르게
    ext = {
        "python": ".py",
        "python3": ".py",
        "py": ".py",
        "js": ".js",
        "ts": ".ts",
    }.get(language.lower(), ".py")

    with tempfile.NamedTemporaryFile(suffix=ext, mode="w", delete=False) as f:
        f.write(source_code)
        tmp_path = f.name

    try:
        proc = subprocess.run(
            [*RUFF_CMD, tmp_path],
            capture_output=True,
            text=True,
            check=False,
        )
        # 0: clean, 1: issues found / 그 외는 실행 오류로 간주
        if proc.returncode not in (0, 1):
            raise RuntimeError(
                f"ruff failed with code {proc.returncode}: {proc.stderr.strip()}"
            )
        if not proc.stdout.strip():
            return []

        issues: List[Dict[str, Any]] = []
        for line in proc.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            parts = line.split(":", 3)
            if len(parts) < 4:
                continue
            _, row_str, col_str, rest = parts
            try:
                row = int(row_str)
                col = int(col_str)
            except ValueError:
                continue
            rest = rest.lstrip(": ").strip()
            if not rest:
                continue
            code_and_msg = rest.split(maxsplit=1)
            if not code_and_msg:
                continue
            code = code_and_msg[0]
            message = code_and_msg[1].strip() if len(code_and_msg) > 1 else ""
            issues.append(
                {
                    "code": code,
                    "message": message,
                    "location": {"row": row, "column": col},
                }
            )

        return issues
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ruff CLI를 찾을 수 없습니다. `pip install ruff` 후 PATH를 확인해 주세요."
        ) from exc
    except Exception as exc:
        raise RuntimeError(f"ruff 실행 중 알 수 없는 오류: {exc}") from exc


_RULE_CODE_PATTERN = re.compile(r"^[A-Z]+[0-9]+$")


def _extract_rule_prefix(code: str) -> str:
    """
    Ruff 규칙 코드에서 알파벳 접두(prefix)를 추출
    """
    m = re.match(r"^([A-Z]+)", code)
    return m.group(1) if m else code


def _compute_quality_from_ruff(issues: List[Dict[str, Any]]) -> List[str]:
    """Ruff 진단을 기반으로 코드 품질 feedback 리스트만 생성"""
    quality_prefixes = {"F", "E", "W", "B", "C", "S", "UP", "A", "TID", "RUF"}
    real_issues: List[Dict[str, Any]] = []
    for issue in issues:
        code = issue.get("code")
        if not isinstance(code, str):
            continue
        if not _RULE_CODE_PATTERN.match(code):
            continue
        prefix = _extract_rule_prefix(code)
        if prefix not in quality_prefixes:
            continue
        real_issues.append(issue)
    if not real_issues:
        return []

    feedback: List[str] = []

    for issue in real_issues:
        code = str(issue.get("code", ""))
        message = str(issue.get("message", "")).strip()
        loc = issue.get("location") or {}
        line = loc.get("row") or loc.get("line") if isinstance(loc, dict) else None
        loc_str = f"(line {line})" if line else ""
        text = f"[{code}] {message} {loc_str}".strip()
        feedback.append(text)

    return feedback[:]


def _compute_collab_from_ruff(issues: List[Dict[str, Any]]) -> List[str]:
    """
    같은 Ruff 결과를 '협업 관점'으로 재해석
    - 네이밍, 복잡도, 스타일 일관성과 관련된 규칙에 더 민감하게 점수 계산
    """
    # 협업 전용 규칙 prefix
    collab_prefixes = {"N", "D", "Q", "I", "ERA"}

    # Ruff 출력 중 실제 규칙 코드만 필터링하고, 협업에 해당하는 것만 남깁니다.
    real_issues: List[Dict[str, Any]] = []
    for issue in issues:
        code = issue.get("code")
        if not isinstance(code, str):
            continue
        if not _RULE_CODE_PATTERN.match(code):
            continue
        prefix = _extract_rule_prefix(code)
        if prefix not in collab_prefixes:
            continue
        real_issues.append(issue)

    if not real_issues:
        return []

    collab_feedback: List[str] = []

    for issue in real_issues:
        code = str(issue.get("code", ""))
        message = str(issue.get("message", "")).strip()
        loc = issue.get("location") or {}
        line = loc.get("row") or loc.get("line") if isinstance(loc, dict) else None
        loc_str = f"(line {line})" if line else ""
        text = f"[{code}] {message} {loc_str}".strip()
        collab_feedback.append(text)

    return collab_feedback[:10]


def _ensure_ruff_issues(state: CodingState) -> List[Dict[str, Any]]:
    """state에 ruff_issues가 없으면 한번 실행해서 채워두고, 있으면 재사용"""
    source_code = (state.get("submitted_code") or state.get("code") or "").strip()
    language = (state.get("language") or "python").strip().lower() or "python"

    if not source_code:
        return []

    # 코드가 변경될 때마다 항상 최신 내용을 기준으로 Ruff를 다시 실행한다.
    # (Redis 체크포인터에 저장된 이전 ruff_issues는 재사용하지 않는다.)
    issues = _run_ruff(source_code, language)
    state["ruff_issues"] = issues
    return issues


def code_quality_agent(state: CodingState) -> CodingState:
    """Ruff 기반 코드 품질 평가"""
    try:
        issues = _ensure_ruff_issues(state)
        feedback = _compute_quality_from_ruff(issues)
        state["code_quality_feedback"] = feedback
    except Exception as exc:
        state["code_quality_error"] = str(exc)
    return state


def collaboration_eval_agent(state: CodingState) -> CodingState:
    """Ruff 결과를 재활용한 협업 능력(코드 관점) 평가"""
    try:
        issues = _ensure_ruff_issues(state)
        feedback = _compute_collab_from_ruff(issues)
        state["collaboration_feedback"] = feedback
    except Exception as exc:
        state["collaboration_error"] = str(exc)
    return state


def code_quality_collabo_agent(state: CodingState) -> CodingState:
    """
    Ruff 한 번 실행 결과로
    - 코드 품질 피드백(code_quality_feedback)
    - 협업 관점 피드백(collaboration_feedback)
    을 한 번에 채워주는 통합 에이전트.
    """
    try:
        issues = _ensure_ruff_issues(state)
        state["code_quality_feedback"] = _compute_quality_from_ruff(issues)
        state["collaboration_feedback"] = _compute_collab_from_ruff(issues)
    except Exception as exc:
        msg = str(exc)
        state["code_quality_error"] = msg
        state["collaboration_error"] = msg
    return state
